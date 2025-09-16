$(function () {
    function checkall(clickchk, relChkbox) {
        var checker = $("#" + clickchk);
        var multichk = $("." + relChkbox);

        checker.click(function () {
            multichk.prop("checked", $(this).prop("checked"));
            $(".show-btn").toggle();
        });
    }

    checkall("contact-check-all", "contact-chkbox");

    $("#input-search").on("keyup", function () {
        var rex = new RegExp($(this).val(), "i");
        $(".search-table .search-items:not(.header-item)").hide();
        $(".search-table .search-items:not(.header-item)")
            .filter(function () {
                return rex.test($(this).text());
            })
            .show();
    });

    $("#btn-add-contact").on("click", function (event) {
        $("#addContactModal #btn-add").show();
        $("#addContactModal #btn-edit").hide();

    });



    function deleteContact() {
        $(".delete").on("click", function (event) {
            event.preventDefault();
            /* Act on the event */
            $(this).parents(".search-items").remove();
        });
    }

    function addContact() {
        $("#btn-add").click(function () {
            var getParent = $(this).parents(".modal-content");

            var $_name = getParent.find("#c-name");
            var $_email = getParent.find("#c-email");
            var $_occupation = getParent.find("#c-occupation");
            var $_phone = getParent.find("#c-phone");
            var $_location = getParent.find("#c-location");

            var $_getValidationField =
                document.getElementsByClassName("validation-text");
            var reg = /^.+@[^\.].*\.[a-z]{2,}$/;
            var phoneReg = /^\d*\.?\d*$/;

            var $_nameValue = $_name.val();
            var $_emailValue = $_email.val();
            var $_occupationValue = $_occupation.val();
            var $_phoneValue = $_phone.val();
            var $_locationValue = $_location.val();

            if ($_nameValue == "") {
                $_getValidationField[0].innerHTML = "Name must be filled out";
                $_getValidationField[0].style.display = "block";
            } else {
                $_getValidationField[0].style.display = "none";
            }

            if ($_emailValue == "") {
                $_getValidationField[1].innerHTML = "Email Id must be filled out";
                $_getValidationField[1].style.display = "block";
            } else if (reg.test($_emailValue) == false) {
                $_getValidationField[1].innerHTML = "Invalid Email";
                $_getValidationField[1].style.display = "block";
            } else {
                $_getValidationField[1].style.display = "none";
            }

            if ($_phoneValue == "") {
                $_getValidationField[2].innerHTML = "Invalid (Enter 10 Digits)";
                $_getValidationField[2].style.display = "block";
            } else if (phoneReg.test($_phoneValue) == false) {
                $_getValidationField[2].innerHTML = "Please Enter A numeric value";
                $_getValidationField[2].style.display = "block";
            } else {
                $_getValidationField[2].style.display = "none";
            }

            if (
                $_nameValue == "" ||
                $_emailValue == "" ||
                reg.test($_emailValue) == false ||
                $_phoneValue == "" ||
                phoneReg.test($_phoneValue) == false
            ) {
                return false;
            }

            var today = new Date();
            var dd = String(today.getDate()).padStart(2, "0");
            var mm = String(today.getMonth()); //January is 0!
            var time = String(today.getTime());
            var yyyy = today.getFullYear();
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
            today = dd + " " + monthNames[mm] + " " + yyyy;
            var cdate = dd + mm + time;

            $html =
                '<tr class="search-items">' +
                '<td class="p-4 ps-0 whitespace-nowrap">' +
                '<div class="n-chk align-self text-center">' +
                '<div class="form-check">' +
                '<input type="checkbox" class="form-check-input rounded contact-chkbox" id="' +
                cdate +
                '">' +
                '<label class="form-check-label" for="' +
                cdate +
                '"></label>' +
                "</div>" +
                "</div>" +
                "</td>" +
                '<td class="p-4 ps-0 whitespace-nowrap">' +
                '<div class="flex items-center">' +
                '<img src="../assets/images/profile/user-1.jpg" alt="avatar" class="rounded-circle h-9 w-9 rounded-full">' +
                '<div class="ms-3">' +
                '<div class="user-meta-info">' +
                '<h6 class="font-semibold text-fs_15 text-dark dark:text-white user-name" data-name=' +
                $_nameValue +
                ">" +
                $_nameValue +
                "</h6>" +
                '<span class="text-fs_15 text-dark font-medium dark:text-darklink user-work" data-occupation=' +
                $_occupationValue +
                ">" +
                $_occupationValue +
                "</span>" +
                "</div>" +
                "</div>" +
                "</div>" +
                "</td>" +
                '<td class="text-fs_15 whitespace-nowrap text-dark font-medium dark:text-darklink p-4">' +
                '<span class="usr-email-addr" data-email=' +
                $_emailValue +
                ">" +
                $_emailValue +
                "</span>" +
                "</td>" +
                '<td class="text-fs_15 whitespace-nowrap text-dark font-medium dark:text-darklink p-4">' +
                '<span class="usr-location" data-location=' +
                $_locationValue +
                ">" +
                $_locationValue +
                "</span>" +
                "</td>" +
                '<td class="text-fs_15 whitespace-nowrap text-dark font-medium dark:text-darklink p-4">' +
                '<span class="usr-ph-no" data-phone=' +
                $_phoneValue +
                ">" +
                $_phoneValue +
                "</span>" +
                "</td>" +
                '<td class="text-fs_15 whitespace-nowrap text-dark font-medium dark:text-darklink p-4">' +
                '<div class="action-btn flex gap-3">' +
                '<a href="javascript:void(0)" class="text-info edit"><i class="ti ti-eye text-lg"></i></a>' +
                '<a href="javascript:void(0)" class="text-dark delete"><i class="ti ti-trash text-lg text-dark font-medium dark:text-darklink"></i></a>' +
                "</div>" +
                "</td>" +
                "</tr>";

            $(".search-table > tbody >tr:first").before($html);
            HSOverlay.close("#addContactModal");

            var $_setNameValueEmpty = $_name.val("");
            var $_setEmailValueEmpty = $_email.val("");
            var $_setOccupationValueEmpty = $_occupation.val("");
            var $_setPhoneValueEmpty = $_phone.val("");
            var $_setLocationValueEmpty = $_location.val("");

            deleteContact();
            editContact();
            checkall("contact-check-all", "contact-chkbox");
        });
    }

    function editContact() {
        $(".edit").on("click", function (event) {
            $("#c #btn-add").hide();
            $("#addContactModal #btn-edit").show();

            // Get Parents
            var getParentItem = $(this).parents(".search-items");
            var getModal = $("#addContactModal");

            // Get List Item Fields
            var $_name = getParentItem.find(".user-name");
            var $_email = getParentItem.find(".usr-email-addr");
            var $_occupation = getParentItem.find(".user-work");
            var $_phone = getParentItem.find(".usr-ph-no");
            var $_location = getParentItem.find(".usr-location");

            // Get Attributes
            var $_nameAttrValue = $_name.attr("data-name");
            var $_emailAttrValue = $_email.attr("data-email");
            var $_occupationAttrValue = $_occupation.attr("data-occupation");
            var $_phoneAttrValue = $_phone.attr("data-phone");
            var $_locationAttrValue = $_location.attr("data-location");

            // Get Modal Attributes
            var $_getModalNameInput = getModal.find("#c-name");
            var $_getModalEmailInput = getModal.find("#c-email");
            var $_getModalOccupationInput = getModal.find("#c-occupation");
            var $_getModalPhoneInput = getModal.find("#c-phone");
            var $_getModalLocationInput = getModal.find("#c-location");

            // Set Modal Field's Value
            var $_setModalNameValue = $_getModalNameInput.val($_nameAttrValue);
            var $_setModalEmailValue = $_getModalEmailInput.val($_emailAttrValue);
            var $_setModalOccupationValue = $_getModalOccupationInput.val(
                $_occupationAttrValue
            );
            var $_setModalPhoneValue = $_getModalPhoneInput.val($_phoneAttrValue);
            var $_setModalLocationValue =
                $_getModalLocationInput.val($_locationAttrValue);
            HSOverlay.open("#addContactModal");

            $("#btn-edit").click(function () {
                var getParent = $(this).parents(".modal-content");

                var $_getInputName = getParent.find("#c-name");
                var $_getInputNmail = getParent.find("#c-email");
                var $_getInputNccupation = getParent.find("#c-occupation");
                var $_getInputNhone = getParent.find("#c-phone");
                var $_getInputNocation = getParent.find("#c-location");

                var $_nameValue = $_getInputName.val();
                var $_emailValue = $_getInputNmail.val();
                var $_occupationValue = $_getInputNccupation.val();
                var $_phoneValue = $_getInputNhone.val();
                var $_locationValue = $_getInputNocation.val();

                var setUpdatedNameValue = $_name.text($_nameValue);
                var setUpdatedEmailValue = $_email.text($_emailValue);
                var setUpdatedOccupationValue = $_occupation.text($_occupationValue);
                var setUpdatedPhoneValue = $_phone.text($_phoneValue);
                var setUpdatedLocationValue = $_location.text($_locationValue);

                var setUpdatedAttrNameValue = $_name.attr("data-name", $_nameValue);
                var setUpdatedAttrEmailValue = $_email.attr("data-email", $_emailValue);
                var setUpdatedAttrOccupationValue = $_occupation.attr(
                    "data-occupation",
                    $_occupationValue
                );
                var setUpdatedAttrPhoneValue = $_phone.attr("data-phone", $_phoneValue);
                var setUpdatedAttrLocationValue = $_location.attr(
                    "data-location",
                    $_locationValue
                );
                HSOverlay.close("#addContactModal");
            });
        });
    }

    $(".delete-multiple").on("click", function () {
        var inboxCheckboxParents = $(".contact-chkbox:checked").parents(
            ".search-items"
        );
        inboxCheckboxParents.remove();
    });

    deleteContact();
    addContact();
    editContact();
});

// Validation Process

var $_getValidationField = document.getElementsByClassName("validation-text");
var reg = /^.+@[^\.].*\.[a-z]{2,}$/;
var phoneReg = /^\d{10}$/;

getNameInput = document.getElementById("c-name");

getNameInput.addEventListener("input", function () {
    getNameInputValue = this.value;

    if (getNameInputValue == "") {
        $_getValidationField[0].innerHTML = "Name Required";
        $_getValidationField[0].style.display = "block";
    } else {
        $_getValidationField[0].style.display = "none";
    }
});

getEmailInput = document.getElementById("c-email");

getEmailInput.addEventListener("input", function () {
    getEmailInputValue = this.value;

    if (getEmailInputValue == "") {
        $_getValidationField[1].innerHTML = "Email Required";
        $_getValidationField[1].style.display = "block";
    } else if (reg.test(getEmailInputValue) == false) {
        $_getValidationField[1].innerHTML = "Invalid Email";
        $_getValidationField[1].style.display = "block";
    } else {
        $_getValidationField[1].style.display = "none";
    }
});

getPhoneInput = document.getElementById("c-phone");

getPhoneInput.addEventListener("input", function () {
    getPhoneInputValue = this.value;

    if (getPhoneInputValue == "") {
        $_getValidationField[2].innerHTML = "Phone Number Required";
        $_getValidationField[2].style.display = "block";
    } else if (phoneReg.test(getPhoneInputValue) == false) {
        $_getValidationField[2].innerHTML = "Invalid (Enter 10 Digits)";
        $_getValidationField[2].style.display = "block";
    } else {
        $_getValidationField[2].style.display = "none";
    }
});