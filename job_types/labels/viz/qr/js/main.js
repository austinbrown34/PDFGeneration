
$(document).ready(function() {
  var img = document.createElement("IMG");
  img.src = "../assets/CC-logo-cutout.gif";
  // console.log('text value is:' + reportdata[0][0]);
  // img = document.getElementById('img-buffer');
  // var img = new Image();
  // var label = "data:image/gif;base64,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"
  // var image = new Image();
  // var canvas = document.createElement('canvas');
  // image.src = "../assets/trump.png";
  // canvas.width = image.naturalWidth;
  // canvas.height = image.naturalHeight;
  // canvas.getContext('2d').drawImage(image, 0, 0);
  // image.src = canvas.toDataURL('image/png');

  var qr_size = reportdimensions[0];
  if (reportdimensions[0] < 55){
    qr_size = 55;
  }

  var el = kjua({
      render: 'image',
      crisp: true,
      size: qr_size,
      fill: '#000000',
      back: '#ffffff',
      ecLevel: 'H',
      rounded: 100,
      quiet: 1,
      mode: 'plain',
      // mSize: 30,
      // mPosX: 50,
      // mPosY: 50,
      text: reportdata[0][0]
      // label: label,
      // fontname: 'sans',
      // fontcolor: '#333',

    // image element
      // image: img
      // image: img

      });
  // document.querySelector('qr').appendChild(el);
  // $('#qr').html(el)
  // forEach(qr.childNodes, function (child) {
  //           qr.removeChild(child);
  //       });
  //       if (el) {
  //           qr.appendChild(el);
  //       }
  el.style.zindex = "-1";
  el.style.position = "relative";
  img.style.zindex = "1";
  img.style.width = qr_size*.4;
  img.style.height = qr_size*.4;
  img.style.display = "block";
  img.style.marginleft = "auto";
  img.style.marginright = "auto";
  img.style.position = "absolute";
  img.style.top = (qr_size - (qr_size*.4))/2;
  img.style.left = (qr_size - (qr_size*.4))/2;
  document.querySelector('#qr').appendChild(el);
  document.querySelector('#qr').appendChild(img);
  // $('#qr').html(el)
  // $('span').html(reportdata[0][0])
    $('#stuff-wrapper').css({
        'width': reportdimensions[0],
        'height': reportdimensions[1],
        'left': reportcoords[0],
        'bottom': reportcoords[1]
    });



    var HeightDiv = $('#stuff-wrapper').height();
    var HeightTable = $('#stuff').height();

    if (HeightTable > HeightDiv) {
        var ZoomAmount = $("#stuff #qr").css("zoom");

        while (HeightTable > HeightDiv && ZoomAmount > .1) {
            console.log('Zoom: ' + ZoomAmount)
            console.log('HeightTable: ' + HeightTable)
            console.log('HeightDiv: ' + HeightDiv)
            ZoomAmount = ZoomAmount - .01;
            $('#stuff #qr').css("zoom", ZoomAmount);
            HeightTable = $('#stuff').height();
        }
    }
});
