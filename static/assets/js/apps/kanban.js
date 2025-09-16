$(function () {
    // ----------------------------------------------------------------------
    // draggble item
    // ----------------------------------------------------------------------
    function kanbanSortable() {
        $('[data-sortable="true"]').sortable({
            connectWith: ".connect-sorting-content",
            items: ".card",
            cursor: "move",
            placeholder: "ui-state-highlight",
            refreshPosition: true,
            stop: function (event, ui) {
                var parent_ui = ui.item.parent().attr("data-item");
            },
            update: function (event, ui) {
                console.log(ui);
                console.log(ui.item);
            },
        });
    }

    // ----------------------------------------------------------------------
    // clear all task on click
    // ----------------------------------------------------------------------
    function clearItem() {
        $(".list-clear-all")
            .off("click")
            .on("click", function (event) {
                event.preventDefault();
                $(this)
                    .parents('[data-action="sorting"]')
                    .find(".connect-sorting-content .card")
                    .remove();
            });
    }

    // ----------------------------------------------------------------------
    // add task and open modal
    // ----------------------------------------------------------------------
    function addKanbanItem() {
        $(".addTask").on("click", function (event) {
            event.preventDefault();
            getParentElement = $(this)
                .parents('[data-action="sorting"]')
                .attr("data-item");
            $(".edit-task-title").hide();
            $(".add-task-title").show();
            $('[data-btn-action="addTask"]').show();
            $('[data-btn-action="editTask"]').hide();
            HSOverlay.open("#addItemModal");
            kanban_add(getParentElement);
        });
    }

    // ----------------------------------------------------------------------
    //   add default item
    // ----------------------------------------------------------------------
    function kanban_add(getParent) {
        $('[data-btn-action="addTask"]')
            .off("click")
            .on("click", function (event) {
                getAddBtnClass = $(this).attr("class").split(" ")[1];

                var today = new Date();
                var dd = String(today.getDate()).padStart(2, "0");
                var mm = String(today.getMonth());

                var monthNames = [
                    "Jan",
                    "Feb",
                    "Mar",
                    "Apr",
                    "May",
                    "Jun",
                    "Jul",
                    "Aug",
                    "Sep",
                    "Oct",
                    "Nov",
                    "Dec",
                ];

                today = dd + " " + monthNames[mm];

                var $_getParent = getParent;

                var itemTitle = document.getElementById("kanban-title").value;
                var itemText = document.getElementById("kanban-text").value;

                item_html =
                    '<div data-draggable="true" class="card img-task" style="">' +
                        '<div class="card-body p-0">' +
                            '<div class="flex items-baseline justify-between py-3 px-3">' +
                                '<h4 class="font-semibold text-dark dark:text-white text-sm cursor-move" data-item-title="' +
                                    itemTitle +
                                '">' +
                                itemTitle +
                                "</h4>" +
                    
                                '<div class="hs-dropdown relative inline-flex"">' +
                                    '<button id="hs-dropdown-tasknew" type="button" class="hs-dropdown-toggle flex justify-center items-center ">' +
                                    '<i class="ti ti-dots-vertical text-bodytext dark:text-darklink "></i>' +
                                    '</button>' +
                                    '<div class="hs-dropdown-menu transition-[opacity,margin] duration hs-dropdown-open:opacity-100 opacity-0 hidden min-w-40 z-[1]" aria-labelledby="hs-dropdown-tasknew">' +
                                        '<div class="flex flex-col">'+
                                            '<div class="py-2 px-4 hover:bg-lightprimary hover:dark:bg-darkprimary">' +            
                                                '<a class="text-sm text-bodytext dark:text-darklink flex gap-2 items-center kanban-item-edit cursor-pointer" href="javascript:void(0);"><i class="ti ti-pencil text-dark dark:text-white text-base"></i>Edit </a>'+
                                            '</div>'+ 
                                            '<div class="py-2 px-4 hover:bg-lightprimary hover:dark:bg-darkprimary">' +            
                                                '<a class="text-sm text-bodytext dark:text-darklink flex gap-2 items-center kanban-item-delete cursor-pointer" href="javascript:void(0);"><i class="ti ti-trash text-dark dark:text-white text-base"></i>Delete </a>'+
                                            '</div>'+     
                                        '</div>'+      
                                    '</div>'+  
                                '</div>'+
                            '</div>'+

                            '<div class="task-content px-3 pb-2">'+
                                '<p class="mb-0" data-item-text="' + itemText + '">' + itemText + "</p>" +
                            '</div>'+

                            '<div class="flex items-center justify-between p-3">'+ 
                                '<a href="javascript:void(0);" class="flex items-center gap-2 text-xs hover:text-primary dark:hover:text-primary" data-item-date="' +
                                    today +
                                    '"><i class="ti ti-calendar text-base"></i>' +
                                    today +
                                '</a>' +
                                '<span class="p-0.5 px-2 rounded-sm text-white bg-primary text-xs">Design</span>'+
                            '</div>' +
                        '</div>'
                    '</div>'


                                

                $("[data-item='" + $_getParent + "'] .connect-sorting-content").append(
                    item_html
                );

                HSOverlay.close("#addItemModal");

                kanbanEdit();
                kanbanDelete();
            });
    }

    // ----------------------------------------------------------------------
    //   add item
    // ----------------------------------------------------------------------
    $("#add-list")
        .off("click")
        .on("click", function (event) {
            event.preventDefault();

            $(".add-list").show();
            $(".edit-list").hide();
            $(".edit-list-title").hide();
            $(".add-list-title").show();
            HSOverlay.open("#addListModal");
        });

    // ----------------------------------------------------------------------
    //   add list
    // ----------------------------------------------------------------------
    $(".add-list")
        .off("click")
        .on("click", function (event) {
            var today = new Date();
            var dd = String(today.getDate()).padStart(2, "0");
            var mm = String(today.getMonth() + 1).padStart(2, "0");

            today = mm + "." + dd;

            var itemTitle = document.getElementById("item-name").value;

            var itemNameLowercase = itemTitle.toLowerCase();
            var itemNameRemoveWhiteSpace = itemNameLowercase.split(" ").join("_");
            var itemDataAttr = itemNameRemoveWhiteSpace;

            item_html =
                '<div data-item="item-' +
                itemDataAttr +
                '" class="task-list-container  w-[302px] shrink-0 mb-4 " data-action="sorting">' +
                '<div class="connect-sorting p-5 bg-gray-200 dark:bg-darkgray rounded-md">' +
                '<div class="task-container-header flex items-center justify-between pb-4">' +
                '<h6 class="font-semibold text-dark dark:text-white text-sm cursor-move" data-item-title="' +
                itemTitle +
                '">' +
                itemTitle +
                "</h6>" +
                '<div class="hstack gap-2">' +
                '<div class="hs-dropdown relative inline-flex">' +
                '<button id="hs-dropdown-task" type="button" class="hs-dropdown-toggle flex justify-center items-center bg-white dark:bg-dark rounded-full h-6 w-6 "><i class="ti ti-dots-vertical text-bodytext dark:text-darklink "></i></button>' +
                '<div class="hs-dropdown-menu transition-[opacity,margin] duration hs-dropdown-open:opacity-100 opacity-0 hidden min-w-40 z-[1]" aria-labelledby="hs-dropdown-task">' +
                '<div class="flex flex-col">'+ 
                '<div class="py-2 px-4 hover:bg-lightprimary hover:dark:bg-darkprimary ">' +  
                '<a class="text-sm text-bodytext dark:text-darklink flex gap-2 items-center list-edit" href="javascript:void(0);">Edit</a>' +
                '</div>'+
                '<div class="py-2 px-4 hover:bg-lightprimary hover:dark:bg-darkprimary ">' +  
                '<a class="text-sm text-bodytext dark:text-darklink flex gap-2 items-center list-delete" href="javascript:void(0);">Delete</a>' +
                '</div>'+
                '<div class="py-2 px-4 hover:bg-lightprimary hover:dark:bg-darkprimary ">' +
                '<a class="text-sm text-bodytext dark:text-darklink flex gap-2 items-center list-delete list-clear-all" href="javascript:void(0);">Clear All</a>' +
                '</div>'+
                '</div>'+ 
                "</div>" +
                "</div>" +
                "</div>" +
                "</div>" +
                '<div class="connect-sorting-content" data-sortable="true">' +
                "</div>" +
                "</div>" +
                "</div>";

            $(".task-list-section").append(item_html);
            HSOverlay.close("#addListModal");
            $("#item-name").val("");
            kanbanSortable();
            editItem();
            deleteItem();
            clearItem();
            addKanbanItem();
            kanbanEdit();
            kanbanDelete();


        });

    // ----------------------------------------------------------------------
    // edit item
    // ----------------------------------------------------------------------
    function editItem() {
        $(".list-edit")
            .off("click")
            .on("click", function (event) {
                event.preventDefault();
                
                var parentItem = $(this);

                $(".add-list").hide();
                $(".edit-list").show();

                $(".add-list-title").hide();
                $(".edit-list-title").show();

                var itemTitle = parentItem
                    .parents('[data-action="sorting"]')
                    .find(".item-head")
                    .attr("data-item-title");
                $("#item-name").val(itemTitle);

                

                $(".edit-list")
                    .off("click")
                    .on("click", function (event) {
                        var $_innerThis = $(this);
                        var $_getListTitle = document.getElementById("item-name").value;

                        var $_editedListTitle = parentItem
                            .parents('[data-action="sorting"]')
                            .find(".item-head")
                            .html($_getListTitle);
                        var $_editedListTitleDataAttr = parentItem
                            .parents('[data-action="sorting"]')
                            .find(".item-head")
                            .attr("data-item-title", $_getListTitle);

                        HSOverlay.close("#addListModal");
                        $("#item-name").val("");
                    });
                HSOverlay.open("#addListModal");
                // $("#addListModal").on("hidden.bs.modal", function (e) {
                //     $("#item-name").val("");
                // });
            });
    }

    // ----------------------------------------------------------------------
    // all list delete
    // ----------------------------------------------------------------------
    function deleteItem() {
        $(".list-delete")
            .off("click")
            .on("click", function (event) {
                event.preventDefault();
                $(this).parents("[data-action]").remove();
            });
    }

    // ----------------------------------------------------------------------
    // Delete item on click
    // ----------------------------------------------------------------------
    function kanbanDelete() {
        $(".kanban-item-delete")
            .off("click")
            .on("click", function (event) {
                event.preventDefault();

                get_card_parent = $(this).parents(".card");
                HSOverlay.open("#deleteConformation");

                $('[data-remove="task"]').on("click", function (event) {
                    event.preventDefault();
                    /* Act on the event */
                    get_card_parent.remove();
                    HSOverlay.close("#deleteConformation");
                });
            });
    }

    // ----------------------------------------------------------------------
    // Edit item on click
    // ----------------------------------------------------------------------
    function kanbanEdit() {
        $(".kanban-item-edit")
            .off("click")
            .on("click", function (event) {
                event.preventDefault();

                var parentItem = $(this);

                $(".add-task-title").hide();
                $(".edit-task-title").show();

                $('[data-btn-action="addTask"]').hide();
                $('[data-btn-action="editTask"]').show();

                var itemKanbanTitle = parentItem
                    .parents(".card")
                    .find("h4")
                    .attr("data-item-title");
                var get_kanban_title = $(".task-text-progress #kanban-title").val(
                    itemKanbanTitle
                );

                var itemText = parentItem
                    .parents(".card")
                    .find('p:not(".progress-count")')
                    .attr("data-item-text");
                var get_kanban_text = $(".task-text-progress #kanban-text").val(
                    itemText
                );

                $('[data-btn-action="editTask"]')
                    .off("click")
                    .on("click", function (event) {
                        var kanbanValueTitle =
                            document.getElementById("kanban-title").value;
                        var kanbanValueText = document.getElementById("kanban-text").value;

                        var itemDataAttr = parentItem
                            .parents(".card")
                            .find("h4")
                            .attr("data-item-title", kanbanValueTitle);
                        var itemKanbanTitle = parentItem
                            .parents(".card")
                            .find("h4")
                            .html(kanbanValueTitle);
                        var itemTextDataAttr = parentItem
                            .parents(".card")
                            .find('p:not(".progress-count")')
                            .attr("data-tasktext", kanbanValueText);
                        var itemText = parentItem
                            .parents(".card")
                            .find('p:not(".progress-count")')
                            .html(kanbanValueText);

                        HSOverlay.close("#addItemModal");
                        var setDate = $(".taskDate").html("");
                        $(".taskDate").hide();
                    });
                HSOverlay.open("#addItemModal");
            });
    }

    editItem();
    deleteItem();
    clearItem();
    addKanbanItem();
    kanbanEdit();
    kanbanDelete();
    kanbanSortable();
});