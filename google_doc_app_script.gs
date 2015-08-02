/**
 * Google Apps Script used to modify Google Docs by inserting links to Trello.
 *
 * See README.md for installation instructions - this script has to be
 * installed manually for big-board-web-hooks to trigger it.
 */


/**
 * Request handler for this Apps Script's published web service.
 * Used to trigger various types of Google Doc updates.
 *
 * Query parameters:
 *    docId: google doc ID to be edited
 *    action: type of document edit being requested
 *        (e.g. "link-to-trello", "populate-retro-doc")
 *
 * Returns a 200 status response w/ "Done!" if successful and
 *  "Error: [explanation]" otherwise.
 *
 * TODO(kamens): change error responses to non-200 status codes once this issue
 * is resolved:
 * https://code.google.com/p/google-apps-script-issues/issues/detail?id=3151
 */
function doGet(e) {
  var docId = e.parameter.docId;

  // Make sure this Google Doc has been granted "anyone in domain can edit"
  var file = null;
  try {
    file = DriveApp.getFileById(docId);
  } catch(err) {
    // File doesn't exist or no access to file whatsoever
    return ContentService.createTextOutput("Error: Cannot find doc");
  }

  var permission = file.getSharingPermission();
  if (!(permission === DriveApp.Permission.EDIT)) {
    return ContentService.createTextOutput("Error: Missing edit permissions");
  }

  var doc = DocumentApp.openById(docId);
  var body = doc.getBody();
  
  // Choose doc editing action based on query param
  switch(e.parameter.action) {
    case 'add-trello-link':
      // Add a link from Google Doc to trello
      linkToTrello(body, e.parameter.trelloURL);
      break;
    case 'remove-trello-links':
      // Remove all trello links from google doc ID. Only used when cleaning up unit tests.
      removeTrelloLinks(body);
      break;
    case 'populate-retro-doc':
      // Populate a retro doc w/ correct title and such
      populateRetroDoc(body, e.parameter.title);
      break;
  }
  
  return ContentService.createTextOutput("Done!");
}


/**
 * Populate the retrospective template w/ various bits of
 * project-specific info (e.g. project title)
 */
function populateRetroDoc(body, title) {
  titleParagraph = findTitleParagraph(body);
  if (titleParagraph) {
    titleParagraph.setText(title);
  }
}


/**
 * Add link from Google Doc to Trello
 *
 * Arguments:
 *    body: Google document body
 *    trelloURL: target trello URL for adding card link
 */
function linkToTrello(body, trelloURL) {
  // Add trello link to google doc, if possible
  var trelloURL = trelloURL;
  if (trelloURL && !alreadyHasTrelloLink(body, trelloURL)) {
    addTrelloLink(body, trelloURL);
  }
}


/**
 * Remove all paragraphs in Google Doc that are links to Trello.
 *
 * This is only used during unit testing to wipe our test docs of any Trello
 * links inserted during unit testing.
 */
function removeTrelloLinks(body) {
  var paragraphs = body.getParagraphs();
  for (var ix = 0; ix < paragraphs.length; ix++) {
    var paragraph = paragraphs[ix];
    var url = paragraph.getLinkUrl();
    if (url && url.indexOf("trello.com") > -1) {
      body.removeChild(paragraph);
    }
  }
}


/**
 * Return True if there's already a link to the right Trello URL in Google Doc
 */
function alreadyHasTrelloLink(body, trelloURL) {
  var paragraphs = body.getParagraphs();
  for (var ix = 0; ix < paragraphs.length; ix++) {
    if (paragraphs[ix].getLinkUrl() === trelloURL) {
      return true;
    }
  }
  return false;
}


/**
 * Find title paragraph in the Google Doc
 *
 * We use this to figure out where to insert the link to Trello
 * and how to style it.
 */
function findTitleParagraph(body) {
  var paragraphs = body.getParagraphs();
  for (var ix = 0; ix < paragraphs.length; ix++) {
    var paragraph = paragraphs[ix];
    var attrs = paragraph.getAttributes();
    if (attrs.HEADING === DocumentApp.ParagraphHeading.TITLE) {
      return paragraph;
    }
  }
  
  return null;
}


/**
 * Populate dictionary of styles that should be copied from the title paragraph
 * to the new Trello link paragraph
 */
function populateStylesFromTitleParagraph(titleParagraph, style) {
  var attrsToCopy = {};
  attrsToCopy[DocumentApp.Attribute.INDENT_START] = true;
  attrsToCopy[DocumentApp.Attribute.INDENT_FIRST_LINE] = true;
  attrsToCopy[DocumentApp.Attribute.INDENT_END] = true;
  attrsToCopy[DocumentApp.Attribute.FONT_FAMILY] = true;
  
  var attrs = titleParagraph.getAttributes();
  for (var key in attrs) {
    if (attrsToCopy[key]) {
      style[key] = attrs[key];
    }
  }
}


/**
 * Add new paragraph to Google Doc w/ link to specified Trello card
 */
function addTrelloLink(body, trelloURL) {
  var indexToInsert = 0;
  var style = {};

  style[DocumentApp.Attribute.FONT_FAMILY] = 'Proxima Nova';  
  style[DocumentApp.Attribute.FONT_SIZE] = 11;
  style[DocumentApp.Attribute.FOREGROUND_COLOR] = '#999999';
  
  var titleParagraph = findTitleParagraph(body);
  if (titleParagraph) {
    indexToInsert = body.getChildIndex(titleParagraph) + 1;
    populateStylesFromTitleParagraph(titleParagraph, style);
  }
  
  // Insert paragraph immediately after title, styled similarly
  var paragraph = body.insertParagraph(indexToInsert,
    'See Trello card for project\'s current status.');
  
  paragraph.setLinkUrl(trelloURL);
  paragraph.setAttributes(style);
}


/**
 * debug utility used when running this script manually from Apps Script editor
 */
function debug() {
  doGet({parameter: {
    action: "add-trello-link",
    docId: "10BqZBGx_PLaj3MtO7rf7VRsbIm2xCk-PeufYzPoerkQ",
    trelloURL: "https://trello.com/c/Owfp15Jo"
  }});
}

