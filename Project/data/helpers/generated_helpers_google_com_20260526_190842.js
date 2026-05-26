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
    await this.page.click("[aria-label=\"Gmail \"]");
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

  // element_id=6, tag=a, stable=false
  async clickLinkGeneric2() {
    await this.page.click("[aria-label=\"Go to Google Home\"]");
  }

  // element_id=7, tag=a, stable=false
  async clickLinkGeneric3() {
    await this.page.click("/html/body/div[2]/div[5]/div/a");
  }

  // element_id=8, tag=div, stable=true
  async waitForDivGeneric() {
    await this.page.waitForSelector("[aria-label=\"Share\"]", { state: 'visible' });
  }

  // element_id=9, tag=a, stable=false
  async clickLinkGeneric4() {
    await this.page.click("/html/body/div[2]/div[5]/div/div[2]/div/div[2]/div/a");
  }

  // element_id=10, tag=a, stable=false
  async clickLinkGeneric5() {
    await this.page.click("/html/body/div[2]/div[5]/div/div[2]/div/div[2]/div/a[2]");
  }

  // element_id=11, tag=a, stable=false
  async clickLinkGeneric6() {
    await this.page.click("/html/body/div[2]/div[5]/div/div[2]/div/div[2]/div/a[3]");
  }

  // element_id=12, tag=a, stable=false
  async clickLinkGeneric7() {
    await this.page.click("/html/body/div[2]/div[5]/div/div[2]/div/div[2]/div/a[4]");
  }

  // element_id=13, tag=a, stable=false
  async clickLinkGeneric8() {
    await this.page.click("/html/body/div[2]/div[5]/div/div[2]/div/div[2]/div/a[5]");
  }

  // element_id=14, tag=button, stable=true
  async clickButtonGeneric() {
    await this.page.click("#spchx");
  }

  // element_id=15, tag=g-left-button, stable=false
  async waitForGGeneric() {
    await this.page.waitForSelector("[aria-label=\"Previous\"]", { state: 'visible' });
  }

  // element_id=16, tag=g-right-button, stable=false
  async waitForGGeneric2() {
    await this.page.waitForSelector("[aria-label=\"Next\"]", { state: 'visible' });
  }

  // element_id=17, tag=button, stable=false
  async clickButtonGeneric2() {
    await this.page.click("[aria-label=\"Add files and tools\"]");
  }

  // element_id=18, tag=button, stable=false
  async clickButtonAddImages() {
    await this.page.click("text=\"Add images\"");
  }

  // element_id=19, tag=button, stable=false
  async clickButtonAddFiles() {
    await this.page.click("text=\"Add files\"");
  }

  // element_id=20, tag=button, stable=false
  async clickButtonAAXUBDisplay() {
    await this.page.click("getByRole('menuitemradio', { name: '.aAXUB{display:flex;align-items:center;justify-con' })");
  }

  // element_id=21, tag=input, stable=false
  async fillInputGeneric(value) {
    await this.page.fill("input", value);
  }

  // element_id=22, tag=input, stable=false
  async fillInputGeneric2(value) {
    await this.page.fill("input", value);
  }

  // element_id=23, tag=textarea, stable=true
  async fillTextareaGeneric(value) {
    await this.page.fill("[name=\"q\"]", value);
  }

  // element_id=24, tag=div, stable=true
  async waitForDivGeneric2() {
    await this.page.waitForSelector("[aria-label=\"Clear\"]", { state: 'visible' });
  }

  // element_id=25, tag=div, stable=true
  async waitForDivGeneric3() {
    await this.page.waitForSelector(".fzj3ad", { state: 'visible' });
  }

  // element_id=26, tag=div, stable=true
  async waitForDivGeneric4() {
    await this.page.waitForSelector(".etxtjc", { state: 'visible' });
  }

  // element_id=27, tag=button, stable=false
  async clickButtonAIMode() {
    await this.page.click("text=\"AI Mode\"");
  }

  // element_id=28, tag=button, stable=false
  async clickButtonGeneric3() {
    await this.page.click("[aria-label=\"Send\"]");
  }

  // element_id=29, tag=button, stable=false
  async clickButtonDBqRkDisplay() {
    await this.page.click("text=\".DBqRk{display:flex;align-self:center;border-radiu\"");
  }

  // element_id=30, tag=span, stable=true
  async waitForSpanGeneric() {
    await this.page.waitForSelector(".Job8vb", { state: 'visible' });
  }

  // element_id=31, tag=div, stable=true
  async waitForDivU48fDWebkit() {
    await this.page.waitForSelector("[aria-label=\"See more\"]", { state: 'visible' });
  }

  // element_id=32, tag=div, stable=false
  async waitForDivJCHpcbHover() {
    await this.page.waitForSelector("text=\".JCHpcb:hover,.LvqzR .JCHpcb{color:#1558d6;text-de\"", { state: 'visible' });
  }

  // element_id=33, tag=div, stable=false
  async waitForDivGeneric5() {
    await this.page.waitForSelector("getByRole('button', { name: 'Word pronunciation' })", { state: 'visible' });
  }

  // element_id=34, tag=div, stable=false
  async waitForDivDelete() {
    await this.page.waitForSelector("getByRole('button', { name: 'Delete' })", { state: 'visible' });
  }

  // element_id=35, tag=div, stable=false
  async waitForDivGeneric6() {
    await this.page.waitForSelector("getByRole('button', { name: 'Word pronunciation' })", { state: 'visible' });
  }

  // element_id=36, tag=input, stable=false
  async fillInputGoogleSearch(value) {
    await this.page.fill("getByRole('button', { name: 'Google Search' })", value);
  }

  // element_id=37, tag=input, stable=false
  async fillInputIM(value) {
    await this.page.fill("text=\"I'm Feeling Lucky\"", value);
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
    await this.page.fill("text=\"I'm Feeling Lucky\"", value);
  }

  // element_id=41, tag=div, stable=true
  async waitForDivGeneric7() {
    await this.page.waitForSelector("[aria-label=\"Close\"]", { state: 'visible' });
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
  async fillInputRKIVaovENJycseMP(value) {
    await this.page.fill("[name=\"ei\"]", value);
  }

  // element_id=45, tag=input, stable=true
  async fillInputAFdpzrgAAAAAahWw(value) {
    await this.page.fill("[name=\"iflsig\"]", value);
  }

  // element_id=46, tag=a, stable=true
  async clickLinkGeneric9() {
    await this.page.click("text=\"हिन्दी\"");
  }

  // element_id=47, tag=a, stable=true
  async clickLinkGeneric10() {
    await this.page.click("text=\"বাংলা\"");
  }

  // element_id=48, tag=a, stable=true
  async clickLinkGeneric11() {
    await this.page.click("text=\"తెలుగు\"");
  }

  // element_id=49, tag=a, stable=true
  async clickLinkGeneric12() {
    await this.page.click("text=\"मराठी\"");
  }

  // element_id=50, tag=a, stable=true
  async clickLinkGeneric13() {
    await this.page.click("text=\"தமிழ்\"");
  }

  // element_id=51, tag=a, stable=true
  async clickLinkGeneric14() {
    await this.page.click("text=\"ગુજરાતી\"");
  }

  // element_id=52, tag=a, stable=true
  async clickLinkGeneric15() {
    await this.page.click("text=\"ಕನ್ನಡ\"");
  }

  // element_id=53, tag=a, stable=true
  async clickLinkGeneric16() {
    await this.page.click("text=\"മലയാളം\"");
  }

  // element_id=54, tag=a, stable=true
  async clickLinkGeneric17() {
    await this.page.click("text=\"ਪੰਜਾਬੀ\"");
  }

  // element_id=55, tag=a, stable=true
  async clickLinkAdvertising() {
    await this.page.click("text=\"Advertising\"");
  }

  // element_id=56, tag=a, stable=true
  async clickLinkBusiness() {
    await this.page.click("text=\"Business\"");
  }

  // element_id=57, tag=a, stable=true
  async clickLinkHowSearch() {
    await this.page.click("text=\"How Search works\"");
  }

  // element_id=58, tag=a, stable=true
  async clickLinkPrivacy() {
    await this.page.click("text=\"Privacy\"");
  }

  // element_id=59, tag=a, stable=true
  async clickLinkTerms() {
    await this.page.click("text=\"Terms\"");
  }

  // element_id=60, tag=div, stable=true
  async waitForDivSettings() {
    await this.page.waitForSelector("text=\"Settings\"", { state: 'visible' });
  }

  // element_id=61, tag=a, stable=true
  async clickLinkSearchSettings() {
    await this.page.click("text=\"Search settings\"");
  }

  // element_id=62, tag=a, stable=true
  async clickLinkAdvancedSearch() {
    await this.page.click("text=\"Advanced search\"");
  }

  // element_id=63, tag=a, stable=true
  async clickLinkYourData() {
    await this.page.click("text=\"Your data in Search\"");
  }

  // element_id=64, tag=a, stable=true
  async clickLinkSearchHistory() {
    await this.page.click("text=\"Search history\"");
  }

  // element_id=65, tag=a, stable=true
  async clickLinkSearchHelp() {
    await this.page.click("text=\"Search help\"");
  }

  // element_id=66, tag=div, stable=true
  async waitForDivDarkTheme() {
    await this.page.waitForSelector(".tFYjZe", { state: 'visible' });
  }

  // element_id=67, tag=textarea, stable=true
  async fillTextareaGeneric2(value) {
    await this.page.fill("[name=\"csi\"]", value);
  }

  // element_id=68, tag=div, stable=false
  async waitForDivGeneric8() {
    await this.page.waitForSelector(".LjfRsf", { state: 'visible' });
  }

  // element_id=69, tag=span, stable=true
  async waitForSpanGeneric2() {
    await this.page.waitForSelector("[aria-label=\"Close\"]", { state: 'visible' });
  }

  // element_id=70, tag=a, stable=false
  async clickLinkGeneric18() {
    await this.page.click(".H3ZkHf.wHYlTd.eJtrMc.Wt5Tfe");
  }

  // element_id=71, tag=a, stable=false
  async clickLinkGeneric19() {
    await this.page.click(".H3ZkHf.wHYlTd.eJtrMc.Wt5Tfe");
  }

  // element_id=72, tag=a, stable=false
  async clickLinkGeneric20() {
    await this.page.click(".H3ZkHf.wHYlTd.eJtrMc.Wt5Tfe");
  }

  // element_id=73, tag=a, stable=false
  async clickLinkGeneric21() {
    await this.page.click(".H3ZkHf");
  }

  // element_id=74, tag=div, stable=false
  async waitForDivGeneric9() {
    await this.page.waitForSelector(".n5Hqzc.ApHyTb.OdBhM.zUdppc", { state: 'visible' });
  }

  // element_id=75, tag=input, stable=false
  async fillInputGeneric3(value) {
    await this.page.fill("[aria-label=\"Share link\"]", value);
  }

  // element_id=76, tag=div, stable=false
  async waitForDivGeneric10() {
    await this.page.waitForSelector(".LjfRsf", { state: 'visible' });
  }

  // element_id=77, tag=div, stable=true
  async waitForDivGeneric11() {
    await this.page.waitForSelector(".k1zIA", { state: 'visible' });
  }

  // element_id=78, tag=div, stable=true
  async waitForDivChooseWhat() {
    await this.page.waitForSelector(".C85rO", { state: 'visible' });
  }

  // element_id=79, tag=div, stable=false
  async waitForDivGeneric12() {
    await this.page.waitForSelector(".Wm2B8c.v0rrvd", { state: 'visible' });
  }

}

module.exports = GeneratedPageHelpers;