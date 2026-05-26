class GeneratedPageHelpers {
  constructor(page) {
    this.page = page;
  }

  // element_id=0, tag=a, stable=true
  async clickLinkAbout() {
    await this.page.click("text=\"About\"");
  }

  // element_id=1, tag=a, stable=true
  async clickLinkStore() {
    await this.page.click("text=\"Store\"");
  }

  // element_id=2, tag=a, stable=true
  async clickLinkGmail() {
    await this.page.click("text=\"Gmail\"");
  }

  // element_id=3, tag=a, stable=true
  async clickLinkImages() {
    await this.page.click("text=\"Images\"");
  }

  // element_id=4, tag=a, stable=true
  async clickLinkGeneric() {
    await this.page.click(".gb_C");
  }

  // element_id=5, tag=a, stable=true
  async clickLinkSignIn() {
    await this.page.click("text=\"Sign in\"");
  }


  // element_id=6, tag=button, stable=true
  async clickButtonAddImages() {
    await this.page.click("text=\"Add images\"");
  }

  // element_id=7, tag=button, stable=true
  async clickButtonAddFiles() {
    await this.page.click("text=\"Add files\"");
  }


  // element_id=8, tag=button, stable=true
  async clickButtonAIMode() {
    await this.page.click("text=\"AI Mode\"");
  }


  // element_id=9, tag=div, stable=false
  async waitForDivDelete() {
    await this.page.waitForSelector("getByRole('button', { name: 'Delete' })", { state: 'visible' });
  }

  // element_id=10, tag=div, stable=false
  async waitForDivGeneric6() {
    await this.page.waitForSelector("getByRole('button', { name: 'Word pronunciation' })", { state: 'visible' });
  }

  // element_id=11, tag=input, stable=false
  async fillInputGoogleSearch(value) {
    await this.page.fill("getByRole('button', { name: 'Google Search' })", value);
  }

  // element_id=12, tag=input, stable=false
  async fillInputIM(value) {
    await this.page.fill("/html/body/div[2]/div[6]/form/div/div/div[3]/div[4]/div[6]/center/input[2]", value);
  }

  // element_id=38, tag=div, stable=true
  async waitForDivReportInappropri() {
    await this.page.waitForSelector(".WzNHm", { state: 'visible' });
  }

  // element_id=39, tag=input, stable=false
  async fillInputGoogleSearch2(value) {
    await this.page.fill("getByRole('button', { name: 'Google Search' })", value);
  }

  // element_id=40, tag=input, stable=false
  async fillInputIM2(value) {
    await this.page.fill("/html/body/div[2]/div[6]/form/div/div/div[4]/center/input[2]", value);
  }

  // element_id=41, tag=div, stable=true
  async waitForDivGeneric7() {
    await this.page.waitForSelector(".NnfpFe", { state: 'visible' });
  }

  // element_id=42, tag=input, stable=true
  async fillInput7d9c60e3220b4d37(value) {
    await this.page.fill("[name=\"sca_esv\"]", value);
  }

  // element_id=43, tag=input, stable=true
  async fillInputHp(value) {
    await this.page.fill("[name=\"source\"]", value);
  }

  // element_id=44, tag=input, stable=true
  async fillInputS6QVau22NOe2vr0P(value) {
    await this.page.fill("[name=\"ei\"]", value);
  }

  // element_id=45, tag=input, stable=true
  async fillInputAFdpzrgAAAAAahWy(value) {
    await this.page.fill("[name=\"iflsig\"]", value);
  }

  // element_id=46, tag=a, stable=true
  async clickLinkGoogleTerms() {
    await this.page.click("text=\"Google Terms of Service\"");
  }

  // element_id=47, tag=a, stable=true
  async clickLinkChromeAnd() {
    await this.page.click("text=\"Chrome and ChromeOS Additional Terms of Service\"");
  }

  // element_id=48, tag=input, stable=true
  async fillInputOn(value) {
    await this.page.fill(".g9jFse", value);
  }

  // element_id=49, tag=a, stable=true
  async clickLinkLearnMore() {
    await this.page.click("text=\"Learn more\"");
  }

  // element_id=50, tag=div, stable=true
  async waitForDivDoNot() {
    await this.page.waitForSelector("text=\"Do not use Chrome\"", { state: 'visible' });
  }

  // element_id=51, tag=div, stable=true
  async waitForDivDownloadChrome() {
    await this.page.waitForSelector("text=\"Download Chrome\"", { state: 'visible' });
  }

  // element_id=52, tag=a, stable=true
  async clickLinkGeneric9() {
    await this.page.click("text=\"हिन्दी\"");
  }

  // element_id=53, tag=a, stable=true
  async clickLinkGeneric10() {
    await this.page.click("text=\"বাংলা\"");
  }

  // element_id=54, tag=a, stable=true
  async clickLinkGeneric11() {
    await this.page.click("text=\"తెలుగు\"");
  }

  // element_id=55, tag=a, stable=true
  async clickLinkGeneric12() {
    await this.page.click("text=\"मराठी\"");
  }

  // element_id=56, tag=a, stable=true
  async clickLinkGeneric13() {
    await this.page.click("text=\"தமிழ்\"");
  }

  // element_id=57, tag=a, stable=true
  async clickLinkGeneric14() {
    await this.page.click("text=\"ગુજરાતી\"");
  }

  // element_id=58, tag=a, stable=true
  async clickLinkGeneric15() {
    await this.page.click("text=\"ಕನ್ನಡ\"");
  }

  // element_id=59, tag=a, stable=true
  async clickLinkGeneric16() {
    await this.page.click("text=\"മലയാളം\"");
  }

  // element_id=60, tag=a, stable=true
  async clickLinkGeneric17() {
    await this.page.click("text=\"ਪੰਜਾਬੀ\"");
  }

  // element_id=61, tag=a, stable=true
  async clickLinkAdvertising() {
    await this.page.click("text=\"Advertising\"");
  }

  // element_id=62, tag=a, stable=true
  async clickLinkBusiness() {
    await this.page.click("text=\"Business\"");
  }

  // element_id=63, tag=a, stable=true
  async clickLinkHowSearch() {
    await this.page.click("text=\"How Search works\"");
  }

  // element_id=64, tag=a, stable=true
  async clickLinkPrivacy() {
    await this.page.click("text=\"Privacy\"");
  }

  // element_id=65, tag=a, stable=true
  async clickLinkTerms() {
    await this.page.click("text=\"Terms\"");
  }

  // element_id=66, tag=div, stable=true
  async waitForDivSettings() {
    await this.page.waitForSelector("text=\"Settings\"", { state: 'visible' });
  }

  // element_id=67, tag=a, stable=true
  async clickLinkSearchSettings() {
    await this.page.click("text=\"Search settings\"");
  }

  // element_id=68, tag=a, stable=true
  async clickLinkAdvancedSearch() {
    await this.page.click("text=\"Advanced search\"");
  }

  // element_id=69, tag=a, stable=true
  async clickLinkYourData() {
    await this.page.click("text=\"Your data in Search\"");
  }

  // element_id=70, tag=a, stable=true
  async clickLinkSearchHistory() {
    await this.page.click("text=\"Search history\"");
  }

  // element_id=71, tag=a, stable=true
  async clickLinkSearchHelp() {
    await this.page.click("text=\"Search help\"");
  }

  // element_id=72, tag=div, stable=true
  async waitForDivDarkTheme() {
    await this.page.waitForSelector(".tFYjZe", { state: 'visible' });
  }

  // element_id=73, tag=textarea, stable=true
  async fillTextareaGeneric2(value) {
    await this.page.fill("[name=\"csi\"]", value);
  }

  // element_id=74, tag=div, stable=false
  async waitForDivGeneric8() {
    await this.page.waitForSelector(".LjfRsf", { state: 'visible' });
  }

  // element_id=75, tag=span, stable=true
  async waitForSpanGeneric2() {
    await this.page.waitForSelector(".xjR8dd", { state: 'visible' });
  }

  // element_id=76, tag=a, stable=false
  async clickLinkGeneric18() {
    await this.page.click(".H3ZkHf.wHYlTd.eJtrMc.Wt5Tfe");
  }

  // element_id=77, tag=a, stable=false
  async clickLinkGeneric19() {
    await this.page.click("/html/body/div[7]/g-dialog/div/div[2]/span/div/div[3]/div/a[2]");
  }

  // element_id=78, tag=a, stable=false
  async clickLinkGeneric20() {
    await this.page.click("/html/body/div[7]/g-dialog/div/div[2]/span/div/div[3]/div/a[3]");
  }

  // element_id=79, tag=a, stable=true
  async clickLinkGeneric21() {
    await this.page.click(".H3ZkHf.wHYlTd.eJtrMc.Wt5Tfe.Q7PwXb");
  }

  // element_id=80, tag=div, stable=true
  async waitForDivGeneric9() {
    await this.page.waitForSelector(".n5Hqzc", { state: 'visible' });
  }

  // element_id=81, tag=input, stable=true
  async fillInputGeneric3(value) {
    await this.page.fill(".baeIxf", value);
  }

  // element_id=82, tag=div, stable=false
  async waitForDivGeneric10() {
    await this.page.waitForSelector("/html/body/div[7]/g-dialog/div/div[2]/div[2]", { state: 'visible' });
  }

  // element_id=83, tag=div, stable=true
  async waitForDivGeneric11() {
    await this.page.waitForSelector(".k1zIA.VntuPb.DYz2A", { state: 'visible' });
  }

  // element_id=84, tag=div, stable=true
  async waitForDivChooseWhat() {
    await this.page.waitForSelector(".C85rO", { state: 'visible' });
  }

  // element_id=85, tag=label, stable=true
  async waitForLabelHelpMake() {
    await this.page.waitForSelector("#promo_data_collection_id", { state: 'visible' });
  }

  // element_id=86, tag=div, stable=true
  async waitForDivGeneric12() {
    await this.page.waitForSelector(".Wm2B8c", { state: 'visible' });
  }

}

module.exports = GeneratedPageHelpers;