$(document).ready(function() {
	$('#example').DataTable( {
			"data": reportdata,
			"paging":   false,
			"ordering": false,
			"info":     false,
			"filter": false,
			"columns": reportcolumns
	} );
	$('#stuff-wrapper').css({
		'width': reportdimensions[0],
		'height': reportdimensions[1],
		'left': reportcoords[0],
		'bottom': reportcoords[1]
	});
	var HeightDiv = $('#stuff-wrapper').height();
	var HeightTable = $('#stuff').height();

	if (HeightTable > HeightDiv){
		var ZoomAmount = $("#stuff table").css("zoom");

		while (HeightTable > HeightDiv && ZoomAmount > .1){
			console.log('Zoom: ' + ZoomAmount)
			console.log('HeightTable: ' + HeightTable)
			console.log('HeightDiv: ' + HeightDiv)
			ZoomAmount = ZoomAmount - .01;
			$('#stuff table').css("zoom", ZoomAmount);
			HeightTable = $('#stuff').height();
		}
	}
	$("#example tr td:first-child").addClass("left");
	if(report_units == '%'){
		$('#example tr td:nth-child(2) span').each(function(){
			if(!$(this).text() == ''){
				if(!$(this).text().match(/[a-z]/i)){
					$(this).append(report_units)
				}
			}

		})

	}

	if(report_units == 'mg/mL'){
		report_units = 'mg/mL';
	}
	if(report_units == 'ppm'){
		report_units = 'PPM';
	}
	if(report_units == 'ppb'){
		report_units = 'PPB';
	}
	if(report_units == 'cfu/g'){
		report_units = 'CFU/g';
	}
	if(secondary_report_units == 'mg/mL'){
		secondary_report_units = 'mg/mL';
	}
	if(secondary_report_units == 'ppm'){
		secondary_report_units = 'PPM';
	}
	if(secondary_report_units == 'ppb'){
		secondary_report_units = 'PPB';
	}
	if(secondary_report_units == 'cfu/g'){
		secondary_report_units = 'CFU/g';
	}
  $(".report_units").html(report_units)
  $(".secondary_report_units").html(secondary_report_units)
// 	$('#example td').attr('id', 'valuetd');
// 	$("#example td").wrapInner("<span></span>");
// 	$(".report_units").html('<div id="valuetd"><span>' + report_units + '</span></div>')
// 	$(".secondary_report_units").html('<div id="valuetd"><span>' + secondary_report_units + '</span></div>')
// 	$('#example #valuetd').textfill({
// 		minFontPixels: 22,
//     maxFontPixels: 26
// });
var multiplier = 1 / parseFloat($("#stuff table").css("zoom"));
var fontsize = (9 * multiplier);
var thfontsize = (10 * multiplier);
var ifontsize = (8 * multiplier);
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
$('#stuff table th i').each(function() {

		$(this).css({
				'font-size': ifontsize + 'px'
		});

})
$('#example tr td:nth-child(2)').each(function() {

		$(this).css({
				'color': '#808080',
				'font-size': ifontsize + 'px'
		});
})
$('#stuff table th:contains("LOQ"),#stuff table th:contains("Limit")').each(function(){
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
} );
