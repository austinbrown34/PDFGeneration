$(document).ready(function() {
    $('#example').DataTable({
        "data": reportdata,
        "paging": false,
        "ordering": false,
        "info": false,
        "filter": false,
        "columns": reportcolumns2
    });
    $('#stuff-wrapper').css({
        'width': reportdimensions[0],
        'height': reportdimensions[1],
        'left': reportcoords[0],
        'bottom': reportcoords[1]
    });
    var HeightDiv = $('#stuff-wrapper').height();
    var HeightTable = $('#stuff').height();

    if (HeightTable > HeightDiv) {
        var ZoomAmount = $("#stuff table").css("zoom");

        while (HeightTable > HeightDiv && ZoomAmount > .1) {
            console.log('Zoom: ' + ZoomAmount)
            console.log('HeightTable: ' + HeightTable)
            console.log('HeightDiv: ' + HeightDiv)
            ZoomAmount = ZoomAmount - .01;
            $('#stuff table').css("zoom", ZoomAmount);
            HeightTable = $('#stuff').height();
        }
    }
    var multiplier = 1 / parseFloat($("#stuff table").css("zoom"));
    var fontsize = (9 * multiplier);
    var thfontsize = (10 * multiplier);
    fontsize = Math.floor(fontsize)
    $('#stuff table tr').each(function() {


        $(this).css({
            'font-size': fontsize + 'px'
        });

    })
    $('#stuff table th').each(function() {


        $(this).css({
            'font-size': fontsize + 'px'
        });

    })
    $('#stuff table th i').each(function() {


        $(this).css({
            'font-size': fontsize + 'px'
        });

    })
    $("#example tr td:first-child").addClass("left");
    $('#example tr td:nth-child(2)').addClass("right");
});
