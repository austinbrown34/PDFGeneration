 /**
 * Create page object
 */
var page = require( 'webpage' ).create(),
    system = require('system');

/**
 * Check for required parameters
 */
if ( system.args.length < 3 ) {
  console.log( 'Usage: report.js <some URL> <output path/filename>' );
  phantom.exit();
}

/**
 * Grab the page and output it to specified target
 */
page.open( system.args[ 1 ], function( status ) {
  console.log( "Status: " + status );

  /**
   * Output the result
   */
  if ( status === "success" ) {
    page.render( system.args[ 2 ] );
    var base64 = page.renderBase64('PNG');
    console.log(base64);
  }

  phantom.exit();
} );
