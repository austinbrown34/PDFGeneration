$(document).ready(function() {
    $('#example').DataTable({
        "data": reportdata,
        "paging": false,
        "ordering": false,
        "info": false,
        "filter": false,
        "columns": reportcolumns
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
    $("#example tr td:first-child").addClass("left");
    if (report_units == '%') {
        $('#example tr td:nth-child(2)').each(function() {
            if (!$(this).text() == '') {
                if (!$(this).text().match(/[a-z]/i)) {
                  if(!$(this).text() == '%'){
                    $(this).append(report_units);
                  }
                }
            }

        })
        $('#example tr td:nth-child(3)').each(function() {
            if (!$(this).text().match(/[a-z]/i)) {
              if(!$(this).text() == '%'){
                $(this).append(report_units);
              }
            }
        })
    }
    if (secondary_report_units == '%') {
        $('#example tr td:nth-child(4)').each(function() {
            if (!$(this).text().match(/[a-z]/i)) {
              if(!$(this).text() == '%'){
                $(this).append(secondary_report_units)
              }
            }
        })
    }
    $("#example td:contains(Total)").each(function() {
        $(this).css({
            'font-family': 'btreb'
        })
        var td2 = $(this).closest("td").next()
        td2.css({
            'font-family': 'btreb'
        })
        var td3 = $(td2).closest("td").next()
        td3.css({
            'font-family': 'btreb'
        })
        var td4 = $(td3).closest("td").next()
        td4.css({
            'font-family': 'btreb'
        })
    })
    $('#example tr td:nth-child(4)').each(function(){
      if($(this).text().match('Fail')){
        $(this).css('color', 'red');
      }
    })
    $('#example tr td:nth-child(5)').each(function(){
      if($(this).text().match('Fail')){
        $(this).css('color', 'red');
      }
    })
    if (report_units == 'mg/mL') {
        report_units = 'mg/mL';
    }
    if (report_units == 'ppm') {
        report_units = 'PPM';
    }
    if (report_units == 'ppb') {
        report_units = 'PPB';
    }
    if (report_units == 'cfu/g') {
        report_units = 'CFU/g';
    }
    if (secondary_report_units == 'mg/mL') {
        secondary_report_units = 'mg/mL';
    }
    if (secondary_report_units == 'ppm') {
        secondary_report_units = 'PPM';
    }
    if (secondary_report_units == 'ppb') {
        secondary_report_units = 'PPB';
    }
    if (secondary_report_units == 'cfu/g') {
        secondary_report_units = 'CFU/g';
    }
    $(".report_units").html(report_units)
    $(".secondary_report_units").html(secondary_report_units)

    var multiplier = 1 / parseFloat($("#stuff table").css("zoom"));
    var fontsize = (9 * multiplier);
    var thfontsize = (10 * multiplier);
    var ifontsize = (7 * multiplier);
    fontsize = Math.floor(fontsize)
    $('#stuff table th:contains("LOQ"),#stuff table th:contains("Limit")').each(function(){
      $(this).css({
          'font-size': ifontsize + 'px',
          'color': '#808080'
      });
    })

    $('#stuff table tr').each(function() {

        $(this).css({
            'font-size': fontsize + 'px'
        });

    })
    $('#stuff table th').each(function() {


        $(this).css({
            'font-size': thfontsize + 'px'
        });

    })

    // $('#stuff table th').each(function(){
    //
    //     $(this).append('<br><i>-</i>');
    //
    // })
    $('#stuff table th i').each(function() {

        $(this).css({
            'font-size': ifontsize + 'px'
        });
        // $(this).remove('span');

    })
    // $('#stuff table th').each(function(){
    //   $(this).next('span').remove();
    //   $(this).next('i').remove();
    // })
    $('#example tr td:nth-child(2)').each(function() {

        $(this).css({
            'color': '#808080',
            'font-size': ifontsize + 'px'
        });
    })

    $('#stuff table th:contains("LOQ"),#stuff table th:contains("Limit"),#stuff table th:contains("Spike")').each(function(){
      $(this).css({
          'font-size': ifontsize + 'px',
          'color': '#808080'
      });

      var columnNo = $(this).index();
      $(this).closest("table")
          .find("tr td:nth-child(" + (columnNo+1) + ")")
          .css({
            'font-size': ifontsize + 'px',
            'color': '#808080'
          });
      })
      $('#stuff table th:contains("LOQ")').each(function(){
        $(this).html("LOQ")
      })
      $('#stuff table th:contains("Limit<")').each(function(){

        $(this).html("Limit")
      })
      $('#stuff table th:contains("Spike")').each(function(){
        $(this).html("Spike")
      })
      $('#stuff table th:contains("Mass")').each(function(){
        $(this).html("Mass")
      })
      $('#stuff table th:contains("Amount")').each(function(){
        $(this).html("Amount")
      })
});
