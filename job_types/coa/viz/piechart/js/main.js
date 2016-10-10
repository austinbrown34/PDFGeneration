jQuery.loadScript = function (url, callback) {
    jQuery.ajax({
        url: url,
        dataType: 'script',
        success: callback,
        async: true
    });
}
$(document).ready(function() {

    $('#stuff-wrapper').css({
        'width': reportdimensions[0],
        'height': reportdimensions[1],
        'left': reportcoords[0],
        'bottom': reportcoords[1]
    });



    var HeightDiv = $('#stuff-wrapper').height();
    var HeightTable = $('#stuff').height();

    if (HeightTable > HeightDiv) {
        var ZoomAmount = $("#stuff #chart").css("zoom");

        while (HeightTable > HeightDiv && ZoomAmount > .1) {
            console.log('Zoom: ' + ZoomAmount)
            console.log('HeightTable: ' + HeightTable)
            console.log('HeightDiv: ' + HeightDiv)
            ZoomAmount = ZoomAmount - .01;
            $('#stuff #chart').css("zoom", ZoomAmount);
            HeightTable = $('#stuff').height();
        }
    }
});


function drawChart() {
    var data = google.visualization.arrayToDataTable(reportdata);

    var options = {
        title: '',
        is3D: true,
        legend: 'none',
        pieSliceText: 'label',
        colors: reportcolors
    };

    var chart = new google.visualization.PieChart(document.getElementById('chart'));
    chart.draw(data, options);
}
$.loadScript('/tmp/job_types/coa/viz/piechart/js/' + report_category + '_colors.js', function(){
  google.charts.load("current", {
      packages: ["corechart"]
  });
  google.charts.setOnLoadCallback(drawChart);
});
