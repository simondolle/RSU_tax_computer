/**
 * Links the "Panier repas" form to the destination Sheet and applies the two
 * settings that the Forms REST API does not expose: response edits + email
 * collection.
 *
 * Edit FORM_ID with the value printed by create_form.py (or in form_info.json).
 * SHEET_ID is the destination spreadsheet given in the task.
 *
 * Run:
 *   clasp run linkAndConfigure
 * or open the script in script.google.com and click Run.
 */

const FORM_ID = 'REPLACE_WITH_FORM_ID';
const SHEET_ID = '1SqykyaboMvX3zBx8YEH5COceqLjHWem7CvHZlqbwTvQ';

function linkAndConfigure() {
  const form = FormApp.openById(FORM_ID);

  form.setAllowResponseEdits(true);
  form.setCollectEmail(false);

  form.setDestination(FormApp.DestinationType.SPREADSHEET, SHEET_ID);

  Logger.log('OK. Responder URL: ' + form.getPublishedUrl());
  Logger.log('Shortened: ' + form.shortenFormUrl(form.getPublishedUrl()));
}
