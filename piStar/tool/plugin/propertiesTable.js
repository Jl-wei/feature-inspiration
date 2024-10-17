ui.components = ui.components || {};  //prevents overriding the variable, while also preventing working with a null variable

ui.components.PropertiesTableView = Backbone.View.extend({
    template: _.template($('#property-template').html()),

    initialize: function () {
        'use strict';

        this.$table = $('#properties-table');

        this.listenTo(this.model, 'mouseup', this.render);
        this.listenTo(this.model, 'change:customProperties', this.render);
        this.listenTo(this.model, 'change:name', this.render);
    },

    render: function () {
        'use strict';

        this.renderElementName();
        this.setupElementNameEditing();

        this.renderElementType();
        this.setupElementTypeEditing();

        for (var propertyName in this.model.prop('customProperties')) {
            this.renderCustomProperty(propertyName);
            this.setupCustomPropertyEditing(propertyName);
        }

        this.setupAddPropertyButton();

        this.clearOptionsPanel();
        if (this.model.isElement() || this.model.isLink()) {
            if (this.model.isKindOfActor()) {
                this.setupCollapseExpandButton();
            }
            else if (this.model.isDependum()) {
                this.setupChangeDirectionButton();
            }
            else if (this.model.isLink()) {
                this.setupClearVerticesButton();
            }
            // Modify start
            else if (this.model.isGoal()) {
                this.setupInspirationButton("LLM");
                this.setupInspirationButton("GP");
            }
            // Modify end

            this.setupDeleteButton();

            if (this.model.isDependum()) {
                this.addInfo('TIP: To change the type of this dependency, just click on the current ' +
                  'Type above and choose a new option.');
            }
            else if (this.model.isContributionLink()) {
                this.addInfo('TIP: To change the label of this contribution link, just click on the current ' +
                  'Value above and choose a new option.');
            }
            else if (this.model.isKindOfActor()) {
                this.addInfo('TIP: To change the type of this Actor, just click on the current ' +
                  'Type above and choose a new option.');
            }
        }
        this.setupOptionsPanel();

        if ($.trim($('#cell-actions').html())) {
            $('#sidepanel-title-actions').show();
        }
        else {
            $('#sidepanel-title-actions').hide();
        }

        return this;
    },

    renderElementName: function () {
        'use strict';

        this.$table.find('tbody').html(this.template({
            propertyName: 'Name',
            propertyValue: this.model.prop('name'),
            dataType: 'text'
        }));
    },
    renderElementType: function () {
        'use strict';

        if (this.model.prop('type')) {
            var propertyName = null;
            if (this.model.isDependum && this.model.isDependum()) {
                propertyName = 'type';
            }
            else if (this.model.isKindOfActor && this.model.isKindOfActor()) {
                propertyName = 'type';
            }
            else if (this.model.isContributionLink && this.model.isContributionLink()) {
                propertyName = 'value';
            }
            if (propertyName) {
                this.$table.find('tbody').append(this.template({
                    propertyName: _.capitalize(propertyName),
                    propertyValue: this.model.prop(propertyName),
                    dataType: 'select'
                }));
            }
        }
    },
    setupElementNameEditing: function () {
        'use strict';

        var currentElementModel = this.model;
        this.$table.find('a').editable({
            showbuttons: 'bottom',
            success: function (response, newValue) {
                currentElementModel.prop('name', newValue);
                return {newValue: currentElementModel.prop('name')};
            }
        })
            .on('shown', function () {
                ui.states.editor.transitionTo(ui.states.editor.EDITING_TEXT);
            })
            .on('hidden', function () {
                ui.states.editor.transitionTo(ui.states.editor.VIEWING);
            });
    },
    setupElementTypeEditing: function () {
        'use strict';

        if (this.model.isDependum && this.model.isDependum()) {
            var typeNames = [];
            var currentType = 0;
            var element = this.model;
            _.forEach(istar.metamodel.nodes, function(nodeType, index) {
                typeNames.push({value: index, text: nodeType.name});
                if (nodeType.name === element.prop('type')) {
                    currentType = index;
                }
            }, this);
            this.$table.find('a').editable({
                showbuttons: false,
                source: typeNames,
                success: function (response, newValue) {
                    var updatedElement = ui.getSelectedCells()[0];
                    var newType = istar.metamodel.nodes[newValue].name;
                    updatedElement.prop('type', newType);
                    var newNode = istar.replaceNode(updatedElement, istar.metamodel.nodes[newValue].name)
                        .prop('isDependum', true);
                    ui.selectCell(newNode);
                    ui.showSelection();
                    ui.collectActionData('edit', 'change', 'change dependum type');
                },
                value: currentType
            })
                .on('shown', function () {
                    ui.states.editor.transitionTo(ui.states.editor.EDITING_TEXT);
                })
                .on('hidden', function () {
                    ui.states.editor.transitionTo(ui.states.editor.VIEWING);
                });
        }
        else if (this.model.isKindOfActor && this.model.isKindOfActor()) {
            var typeNames = [];
            var currentType = 0;
            var element = this.model;
            _.forEach(istar.metamodel.containers, function(elementType, index) {
                typeNames.push({value: index, text: elementType.name});
                if (elementType.name === element.prop('type')) {
                    currentType = index;
                }
            }, this);
            this.$table.find('a').editable({
                showbuttons: false,
                source: typeNames,
                success: function (response, newValue) {
                    var updatedElement = ui.getSelectedCells()[0];
                    var newType = istar.metamodel.containers[newValue].name;
                    // updatedElement.prop('type', newType);
                    var result = istar.replaceNode(updatedElement, istar.metamodel.containers[newValue].name);
                    if (result.ok === false) {
                        ui.displayInvalidLinkMessage('it is not possible to change this <b>' +
                            element.prop('type') + '</b> to <b>' + newType +
                            '</b>, because it would violate the following constraint:<br /><br />' +
                            result.isValid.message);
                    }
                    else {
                        ui.selectCell(result);
                        ui.showSelection();
                        ui.collectActionData('edit', 'change', 'change actor type');
                    }
                },
                value: currentType
            })
              .on('shown', function () {
                  ui.states.editor.transitionTo(ui.states.editor.EDITING_TEXT);
              })
              .on('hidden', function () {
                  ui.states.editor.transitionTo(ui.states.editor.VIEWING);
              });
        }
        else if (this.model.isContributionLink && this.model.isContributionLink()) {
            var element = this.model;
            var contributionMetamodel = istar.metamodel.nodeLinks.ContributionLink;
            var valueNames = contributionMetamodel.possibleLabels;
            // var currentType = _.findIndex(valueNames, function(o) { return o === element.prop('value'); });
            this.$table.find('a').editable({
                showbuttons: false,
                source: valueNames,
                success: function (response, newValue) {
                    ui.getSelectedCells()[0].prop('value', newValue);
                    ui.collectActionData('edit', 'change', 'change contribution value');
                },
                value: element.prop('value')
            })
                .on('shown', function () {
                    ui.states.editor.transitionTo(ui.states.editor.EDITING_TEXT);
                })
                .on('hidden', function () {
                    ui.states.editor.transitionTo(ui.states.editor.VIEWING);
                });
        }
        // else {
        //     this.$table.find('a').editable({
        //         disabled: true,
        //     });
        // }
    },
    setupAddPropertyButton: function () {
        'use strict';

        $('#add-property-button-area').html('<a href="#" id="add-property-button" class="property-add" data-type="text" data-pk="1"           data-name="name" data-title="Enter description" data-placeholder="ahhhh" title="Add a new property to this element">        <span class="glyphicon glyphicon-plus-sign" aria-hidden="true"></span>        Add Property</a>');
        // $('#add-property-button-area').html('<button type="button" id="addPropertyButton">Add Property</button>');
        // $('#cell-buttons').html('<button type="button" id="addPropertyButton">Add Property</button>');
        $('#add-property-button').click(function (e) {
            var newPropertyName = window.prompt('Name of the new custom property:', 'newProperty');
            if (newPropertyName) {
                var isValidName = false;
                var validityMessage = '';
                if (isNaN(newPropertyName)) {
                    var existsPropertyWithSameNameInThisElement = ui.getSelectedCells()[0].prop('customProperties/' + newPropertyName);
                    if (existsPropertyWithSameNameInThisElement === undefined) {
                        newPropertyName = newPropertyName.replace(/\W/g, '');
                        isValidName = true;
                    }
                    else {
                        validityMessage = 'A property with this same name has already been defined; please try again with a different name';
                    }
                }
                else {
                    validityMessage = 'Sorry, the name of a property cannot be a number; please try again with a different name';
                }

                if (isValidName) {
                    ui.getSelectedCells()[0].prop('customProperties/' + newPropertyName, '');
                }
                else {
                    ui.alert(validityMessage, 'Invalid property name');
                }
            }
            ui.collectActionData('click', e.currentTarget.id);
        });
    },
    clearOptionsPanel: function () {
        'use strict';

        $('#cell-actions').html('');
    },
    setupCollapseExpandButton: function () {
        'use strict';

        $('#cell-actions').append(
            '<a id="collapse-expand-actor-button" class="btn btn-default btn-xs button-horizontal" title="Shortcut: alt+click the actor">Collapse/Expand</a><br>'
        );
        $('#collapse-expand-actor-button').click(function (e) {
            if (ui.getSelectedCells()) {
                ui.hideSelection();//remove the focus from the actor
                ui.getSelectedCells()[0].toggleCollapse();
                ui.showSelection();//give the focus back to actor, now collapsed or expanded
            }

            ui.collectActionData('click', e.currentTarget.id);
        });
    },
    setupChangeDirectionButton: function () {
        'use strict';

        if (ui.getSelectedCells()[0].remove) {
            $('#cell-actions').append(
                '<a id="flip-direction-button" class="btn btn-default btn-xs button-horizontal" title="Change the direction of the dependency">Flip direction</a><br>'
            );
            $('#flip-direction-button').click(function (e) {
                var dependum = ui.getSelectedCells()[0];
                if (dependum) {
                    var connectedLinks = istar.graph.getConnectedLinks(dependum);

                    //first verify whether the flipped dependency would be valid
                    var source = connectedLinks[0].getSourceElement();
                    var target = connectedLinks[1].getTargetElement();
                    if (source === dependum) {
                        source = connectedLinks[1].getSourceElement();
                        target = connectedLinks[0].getTargetElement();
                    }
                    var isValid = istar.metamodel.dependencyLinks['DependencyLink'].isValid(target, source);//check with flipped source/target
                    // isValid = istar.types['DependencyLink'].isValid(target, source);//check with flipped source/target

                    if (isValid.isValid) {
                        //If we change the source and target without removing the vertices, the math for creating
                        //the curves may throw exceptions. Thus, we store them in a temp variable, and then re-add
                        //them reversed.
                        //It is reversed because the direction has changed, thus the first vertex is now the last vertex,
                        //and so on.
                        var originalVertices = connectedLinks[0].vertices();
                        var originalSource = connectedLinks[0].prop('source/id');
                        connectedLinks[0].vertices([]);
                        connectedLinks[0].prop('source/id', connectedLinks[0].prop('target/id'));
                        connectedLinks[0].prop('target/id', originalSource);
                        if (istar.graph.getCell(originalSource).isKindOfActor()) {
                            connectedLinks[0].prop('target/selector', 'actorSymbol');
                        } else {
                            connectedLinks[0].prop('target/selector', 'text');
                        }
                        if (istar.graph.getCell(connectedLinks[0].prop('source/id')).isKindOfActor()) {
                            connectedLinks[0].prop('source/selector', 'actorSymbol');
                        } else {
                            connectedLinks[0].prop('source/selector', 'text');
                        }
                        connectedLinks[0].vertices(_.reverse(originalVertices));


                        originalVertices = connectedLinks[1].vertices();
                        connectedLinks[1].vertices([]);
                        originalSource = connectedLinks[1].prop('source/id');
                        connectedLinks[1].prop('source/id', connectedLinks[1].prop('target/id'));
                        connectedLinks[1].prop('target/id', originalSource);
                        if (istar.graph.getCell(originalSource).isKindOfActor()) {
                            connectedLinks[1].prop('target/selector', 'actorSymbol');
                        } else {
                            connectedLinks[1].prop('target/selector', 'text');
                        }
                        if (istar.graph.getCell(connectedLinks[1].prop('source/id')).isKindOfActor()) {
                            connectedLinks[1].prop('source/selector', 'actorSymbol');
                        } else {
                            connectedLinks[1].prop('source/selector', 'text');
                        }
                        connectedLinks[1].vertices(_.reverse(originalVertices));
                        ui.selectCell(dependum);
                    }
                    else {
                        ui.displayInvalidLinkMessage(isValid.message + '. Thus, this Dependency currently cannot be flipped');
                    }
                }
                ui.collectActionData('click', e.currentTarget.id);
            });
        }
    },
    setupClearVerticesButton: function () {
        'use strict';

        $('#cell-actions').append(
            '<a id="clear-vertices-button" class="btn btn-default btn-xs button-horizontal" ' +
            'title="This deletes all vertices in this link. To delete an individual vertex, double click the vertex.">Clear vertices</a><br>'
        );
        $('#clear-vertices-button').click(function (e) {
            if (ui.getSelectedCells()) {
                ui.getSelectedCells()[0].vertices([]);
            }
            ui.collectActionData('click', e.currentTarget.id);
        });
    },
    setupDeleteButton: function () {
        'use strict';

        if (ui.getSelectedCells()[0].remove) {
            $('#cell-actions').append(
                '<a id="delete-element-button" class="btn btn-default btn-xs button-horizontal" title="Shortcut: Delete key">Delete</a><br>'
            );
            $('#delete-element-button').click(function (e) {
                if (ui.getSelectedCells()) {
                    ui.deleteCell(ui.getSelectedCells()[0]);
                }
                ui.collectActionData('click', e.currentTarget.id);
            });
        }
    },
    setupOptionsPanel: function () {
        'use strict';

        if (this.model.prop('backgroundColor')) {
            $('#single-element-color-picker').get(0).jscolor.fromString(this.model.prop('backgroundColor'));
        }
        else if (ui.getSelectedCells()){
            $('#single-element-color-picker').get(0).jscolor.fromString(ui.defaultElementBackgroundColor);
        }
    },
    addInfo: function (content) {
        'use strict';

        $('#cell-actions').append(
          '<i>' + content + '</i><br>'
        );
    },
    renderCustomProperty: function (propertyName) {
        'use strict';

        this.$table.find('tbody').append(this.template({
            propertyName: propertyName,
            propertyValue: this.model.prop('customProperties/' + propertyName),
            dataType: 'textarea'
        }));
    },
    setupCustomPropertyEditing: function (propertyName) {
        'use strict';

        $('#current' + propertyName).editable({
                showbuttons: 'bottom',
                success: function (response, newValue) {
                    //update backbone model
                    var updatedElement = ui.changeCustomPropertyValue(ui.getSelectedCells()[0], $(this).attr('data-name'), newValue);
                    return {newValue: updatedElement.prop('customProperties/' + propertyName)};
                }
            }
        )
            .on('shown', function () {
                ui.states.editor.transitionTo(ui.states.editor.EDITING_TEXT);
            })
            .on('hidden', function () {
                ui.states.editor.transitionTo(ui.states.editor.VIEWING);
            });
    },
    setupInspirationButton: function (source) {
        'use strict';
    
        let api_key = "custom-api-key";

        let currentNode = ui.getSelectedCells()[0];
        source = source.toLowerCase();
        let buttonName = ""
        if (source == "gp") {
            buttonName = "Inspire from AppStore"
        } else {
            buttonName = "Inspire from LLM"
        }
        if (currentNode.isGoal()) {
            $('#cell-actions').append(
                `<a id="${source}-inspire-element-button" class="btn btn-default btn-xs button-horizontal" title="Shortcut: Inspire key">${buttonName}</a><br>`
            );
            $(`#${source}-inspire-element-button`).click(function (e) {
                ui.collectActionData('click', e.currentTarget.id);

                let nodeColor = "#D5CDFF"
                if (source == "gp") {
                    nodeColor = "#FFFF99";
                }
                let query = {"source": source};
                query["feature"] = currentNode.attributes["name"];
                query["feature_description"] = currentNode.attributes.customProperties["Description"];
                if (istar.graph.getNeighbors(currentNode, {outbound: true}).length > 0) {
                    let superNode = istar.graph.getNeighbors(currentNode, {outbound: true})[0];
                    if (superNode.isGoal()) {
                        query["super_feature"] = superNode.attributes["name"];
                        query["super_feature_description"] = superNode.attributes.customProperties["Description"];
                        let friendNodes = istar.graph.getNeighbors(superNode, {inbound: true});
                        query["sibling_features"] = friendNodes.map((node) => {return {"sub-feature": node.attributes["name"], "description": node.attributes.customProperties["Description"]}});
                    }
                }
                console.log(query);
                query["api_key"] = api_key;
                let currentX = currentNode.position()['x'];
                let currentY = currentNode.position()['y'];
                fetch(`http://localhost:12345/inspire?` + new URLSearchParams({query: JSON.stringify(query)}), 
                    {method: 'GET'})
                    .then(result => result.json())
                    .then(subFeatures => {
                        console.log(subFeatures);
                        let start_x = currentX - (subFeatures.length * 80) / 2;
                        let i = 0;
                        for (const subFeature of subFeatures) {
                            let subGoal = istar.addGoal(
                                subFeature['sub-feature'],
                                {position: {x: start_x + 100*i, y: currentY + 70}}
                            );
                            subGoal.attr(".element/fill", nodeColor);
                            subGoal.prop('backgroundColor', nodeColor)
                            subGoal.prop('customProperties/Description', subFeature['description']);
                            if ('source-app-id' in subFeature) {
                                subGoal.prop(
                                    'customProperties/AppId', subFeature['source-app-id']
                                    // "https://play.google.com/store/apps/details?id=" + subFeature['source-app-id']
                                );
                            }
                            istar.embedNode(subGoal, currentNode.getParentCell());
                            istar.addAndRefinementLink(subGoal, currentNode);
                            i += 1;
                        }
                    })
                    .catch(errorMsg => { console.log(errorMsg); });
            });
        }
    }
});
