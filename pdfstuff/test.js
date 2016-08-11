function get_sidebar() {
  originalSpreadsheet = SpreadsheetApp.getActive();
  originalSpreadsheet.toast('Retrieving Orders...', 'Status', 5);

  // Setting up Globals


  ClientJobSheet = originalSpreadsheet.getSheetByName("Merge Data");
  CCoutSheet = originalSpreadsheet.getSheetByName("C.C.");
  col = 1;
  row = 1;

  num_of_samples = 0;
  open_orders = [];
  range_values_sample_ids = {};
  range_input_values_sample_ids = {};

  update_ids = {};

  Clients = getClients();
  Clients.then(function(Clients){ClientOrders = getOrders(Clients);})
  .then(function(ClientOrders){for (var property in ClientOrders) {open_orders.push({name: property, functionName: 'get_this_job_' + property});}})
  .then(function(open_orders){var html = HtmlService.createHtmlOutputFromFile('Page').setTitle('Orders to Complete').setWidth(400); SpreadsheetApp.getUi().showSidebar(html);});

}
