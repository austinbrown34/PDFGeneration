function waitFor( page, selector, expiry, callback ) {
    system.stderr.writeLine( "- waitFor( " + selector + ", " + expiry + " )" );

    // try and fetch the desired element from the page
    var result = page.evaluate(
        function (selector) {
            return document.querySelector( selector );
        }, selector
    );

    // if desired element found then call callback after 50ms
    if ( result ) {
        system.stderr.writeLine( "- trigger " + selector + " found" );
        window.setTimeout(
            function () {
                callback( true );
            },
            50
        );
        return;
    }

    // determine whether timeout is triggered
    var finish = (new Date()).getTime();
    if ( finish > expiry ) {
        system.stderr.writeLine( "- timed out" );
        callback( false );
        return;
    }

    // haven't timed out, haven't found object, so poll in another 100ms
    window.setTimeout(
        function () {
            waitFor( page, selector, expiry, callback );
        },
        100
    );
}

var page = require( 'webpage' ).create(),
   system = require('system');

page.paperSize = {
  format: 'A4',
  orientation: 'portrait',
  margin: '0cm'
};
var settings = {
  encoding: "utf8"
};
if ( system.args.length < 3 ) {
 console.log( 'Usage: report.js <some URL> <output path/filename>' );
 phantom.exit();
}

page.open( system.args[ 1 ], settings, function( status ) {
  waitFor(
    page,
    "#chart", // wait for this object to appear
    (new Date()).getTime() + 5000, // timeout at 5 seconds from now
    function (status) {
        system.stderr.writeLine( "- submission status: " + status );
        page.render( system.args[ 2 ] );
      //  process_rows( page );
        if ( status === "success" ) {
            // success, element found by waitFor()
             page.render( system.args[ 2 ] );
            // process_rows( page );
        } else {
            // waitFor() timed out
            phantom.exit( 1 );
        }
    }
);

//  console.log( "Status: " + status );
//  if ( status === "success" ) {
//  window.setTimeout(function() {
//
//
//    var results = page.evaluate(function(){ return document.getElementById('chart').innerHTML })
// console.log(results);
// page.render( system.args[ 2 ] );
//  phantom.exit();
// }, 1000);
//  }
} );
