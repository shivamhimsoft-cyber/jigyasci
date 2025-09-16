$(function () {
    function removeNote() {
        $(".remove-note")
            .off("click")
            .on("click", function (event) {
                event.stopPropagation();
                $(this).parents(".single-note-item").remove();
            });
    }

    function favouriteNote() {
        $(".favourite-note")
            .off("click")
            .on("click", function (event) {
                event.stopPropagation();
                $(this).parents(".single-note-item").toggleClass("note-favourite");
            });
    }

    var $btns = $(".note-link").click(function () {
        if (this.id == "all-category") {
            var $el = $("." + this.id).fadeIn();
            $("#note-full-container > div").not($el).hide();
        }
        if (this.id == "important") {
            var $el = $("." + this.id).fadeIn();
            $("#note-full-container > div").not($el).hide();
        } else {
            var $el = $("." + this.id).fadeIn();
            $("#note-full-container > div").not($el).hide();
        }
        $btns.removeClass("active");
        $(this).addClass("active");
    });

    $("#add-notes").on("click", function (event) {
        HSOverlay.open("#notes-modal");
        $("#btn-n-save").hide();
        $("#btn-n-add").show();
    });

    // Button add
    $("#btn-n-add").on("click", function (event) {
        event.preventDefault();
        /* Act on the event */
        var today = new Date();
        var dd = String(today.getDate()).padStart(2, "0");
        var mm = String(today.getMonth()); //January is 0!
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

        var $_noteTitle = document.getElementById("note-has-title").value;
        var $_noteDescription = document.getElementById(
            "note-has-description"
        ).value;

        $html =
            '<div class="lg:col-span-4 md:col-span-4 sm:col-span-6 single-note-item all-category"><div class="card card-body sm:px-7">' +
            '<span class="side-stick"></span>' +
            '<h6 class="font-medium text-sm text-dark dark:text-white" data-noteHeading="' +
            $_noteTitle +
            '">' +
            $_noteTitle +
            '</h6>' +
            '<p class="note-date text-xs">' +
            today +
            "</p>" +
            '<div class="note-content mt-3">' +
            '<p class="note-inner-content text-sm" data-noteContent="' +
            $_noteDescription +
            '">' +
            $_noteDescription +
            "</p>" +
            "</div>" +
            '<div class="flex items-center mt-3">' +
                '<a href="javascript:void(0)" class="link me-1"><i class="ti ti-star text-base favourite-note text-dark dark:text-darklink hover:text-primary dark:hover:text-primary"></i></a>' +
                '<a href="javascript:void(0)" class="link text-error ms-2"><i class="ti ti-trash text-base remove-note"></i></a>' +
            "</div>"+
            "</div> ";

        $("#note-full-container").prepend($html);
        HSOverlay.close("#notes-modal");
       

        removeNote();
        favouriteNote();
       
    });

    removeNote();
    favouriteNote();

    $("#btn-n-add").attr("disabled", "disabled");
});

$("#note-has-title").keyup(function () {
    var empty = false;
    $("#note-has-title").each(function () {
        if ($(this).val() == "") {
            empty = true;
        }
    });

    if (empty) {
        $("#btn-n-add").attr("disabled", "disabled");
    } else {
        $("#btn-n-add").removeAttr("disabled");
    }
});