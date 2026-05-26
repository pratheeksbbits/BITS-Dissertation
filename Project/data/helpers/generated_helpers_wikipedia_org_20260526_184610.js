class GeneratedPageHelpers {
  constructor(page) {
    this.page = page;
  }

  // element_id=0, tag=h1, stable=true
  async waitForH1WikipediaTheFreeEncyclopedia() {
    await this.page.waitForSelector(".central-textlogo-wrapper", { state: 'visible' });
  }

  // element_id=1, tag=strong, stable=true
  async waitForStrongTheFreeEncyclopedia() {
    await this.page.waitForSelector("text=\"The Free Encyclopedia\"", { state: 'visible' });
  }

  // element_id=2, tag=strong, stable=false
  async waitForStrongEnglish() {
    await this.page.waitForSelector("text=\"English\"", { state: 'visible' });
  }

  // element_id=3, tag=strong, stable=false
  async waitForStrongGeneric() {
    await this.page.waitForSelector("/html/body/main/nav/div[2]/a/strong", { state: 'visible' });
  }

  // element_id=4, tag=strong, stable=false
  async waitForStrongDeutsch() {
    await this.page.waitForSelector("/html/body/main/nav/div[3]/a/strong", { state: 'visible' });
  }

  // element_id=5, tag=strong, stable=false
  async waitForStrongFranAis() {
    await this.page.waitForSelector("/html/body/main/nav/div[4]/a/strong", { state: 'visible' });
  }

  // element_id=6, tag=strong, stable=false
  async waitForStrongGeneric2() {
    await this.page.waitForSelector("/html/body/main/nav/div[5]/a/strong", { state: 'visible' });
  }

  // element_id=7, tag=strong, stable=false
  async waitForStrongGeneric3() {
    await this.page.waitForSelector("/html/body/main/nav/div[6]/a/strong", { state: 'visible' });
  }

  // element_id=8, tag=strong, stable=false
  async waitForStrongEspaOl() {
    await this.page.waitForSelector("/html/body/main/nav/div[7]/a/strong", { state: 'visible' });
  }

  // element_id=9, tag=strong, stable=false
  async waitForStrongItaliano() {
    await this.page.waitForSelector("/html/body/main/nav/div[8]/a/strong", { state: 'visible' });
  }

  // element_id=10, tag=strong, stable=false
  async waitForStrongPolski() {
    await this.page.waitForSelector("/html/body/main/nav/div[9]/a/strong", { state: 'visible' });
  }

  // element_id=11, tag=strong, stable=false
  async waitForStrongPortuguS() {
    await this.page.waitForSelector("/html/body/main/nav/div[10]/a/strong", { state: 'visible' });
  }

  // element_id=12, tag=label, stable=true
  async waitForLabelSearchWikipedia() {
    await this.page.waitForSelector("text=\"Search Wikipedia\"", { state: 'visible' });
  }

  // element_id=13, tag=label, stable=true
  async waitForLabelEN() {
    await this.page.waitForSelector("#jsLangLabel", { state: 'visible' });
  }

  // element_id=14, tag=h2, stable=false
  async waitForH2Generic() {
    await this.page.waitForSelector(".bookshelf-container", { state: 'visible' });
  }

  // element_id=15, tag=h2, stable=false
  async waitForH2Generic2() {
    await this.page.waitForSelector("/html/body/main/nav[2]/div[3]/div/h2[2]", { state: 'visible' });
  }

  // element_id=16, tag=h2, stable=false
  async waitForH2Generic3() {
    await this.page.waitForSelector("/html/body/main/nav[2]/div[3]/div/h2[3]", { state: 'visible' });
  }

  // element_id=17, tag=h2, stable=false
  async waitForH2Generic4() {
    await this.page.waitForSelector("/html/body/main/nav[2]/div[3]/div/h2[4]", { state: 'visible' });
  }

  // element_id=18, tag=h2, stable=false
  async waitForH2Generic5() {
    await this.page.waitForSelector("/html/body/main/nav[2]/div[3]/div/h2[5]", { state: 'visible' });
  }

  // element_id=19, tag=h3, stable=true
  async waitForH3WeOweYouAnExplanation() {
    await this.page.waitForSelector("h3", { state: 'visible' });
  }

  // element_id=20, tag=strong, stable=false
  async waitForStrongThereAreNoSmallContributionsEvery() {
    await this.page.waitForSelector("text=\"There are no small contributions: every edit count\"", { state: 'visible' });
  }

  // element_id=21, tag=strong, stable=true
  async waitForStrongDownloadWikipediaForAndroidOrIOS() {
    await this.page.waitForSelector("text=\"Download Wikipedia for Android or iOS\"", { state: 'visible' });
  }

}

module.exports = GeneratedPageHelpers;