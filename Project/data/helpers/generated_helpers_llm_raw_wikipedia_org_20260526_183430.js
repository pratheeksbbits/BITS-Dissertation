class GeneratedPageHelpers {
  constructor(page) {
    this.page = page;
  }

  // Interact with the Wikipedia logo
  async clickCentralTextLogoWrapperElementId0() {
    await this.page.click('.central-textlogo-wrapper');
  }

  // Assert visibility of "The Free Encyclopedia"
  async assertVisibleTheFreeEncyclopediaElementId1() {
    await this.page.waitForSelector('text="The Free Encyclopedia"', { state: 'visible' });
  }

  // Assert visibility of "English"
  async assertVisibleEnglishElementId2() {
    await this.page.waitForSelector('text="English"', { state: 'visible' });
  }

  // Click on "日本語"
  async clickJapaneseElementId3() {
    await this.page.click('/html/body/main/nav/div[2]/a/strong');
  }

  // Click on "Deutsch"
  async clickGermanElementId4() {
    await this.page.click('/html/body/main/nav/div[3]/a/strong');
  }

  // Click on "Français"
  async clickFrenchElementId5() {
    await this.page.click('/html/body/main/nav/div[4]/a/strong');
  }

  // Click on "Русский"
  async clickRussianElementId6() {
    await this.page.click('/html/body/main/nav/div[5]/a/strong');
  }

  // Click on "中文"
  async clickChineseElementId7() {
    await this.page.click('/html/body/main/nav/div[6]/a/strong');
  }

  // Click on "Español"
  async clickSpanishElementId8() {
    await this.page.click('/html/body/main/nav/div[7]/a/strong');
  }

  // Click on "Italiano"
  async clickItalianElementId9() {
    await this.page.click('/html/body/main/nav/div[8]/a/strong');
  }

  // Click on "Polski"
  async clickPolishElementId10() {
    await this.page.click('/html/body/main/nav/div[9]/a/strong');
  }

  // Click on "Português"
  async clickPortugueseElementId11() {
    await this.page.click('/html/body/main/nav/div[10]/a/strong');
  }

  // Assert visibility of "Search Wikipedia"
  async assertVisibleSearchWikipediaElementId12() {
    await this.page.waitForSelector('text="Search Wikipedia"', { state: 'visible' });
  }

  // Assert visibility of "EN" language label
  async assertVisibleLanguageLabelElementId13() {
    await this.page.waitForSelector('#jsLangLabel', { state: 'visible' });
  }

  // Assert visibility of bookshelf container
  async assertVisibleBookshelfContainerElementId14() {
    await this.page.waitForSelector('.bookshelf-container', { state: 'visible' });
  }

  // Assert visibility of h2 element (elementId15)
  async assertVisibleH2ElementId15() {
    await this.page.waitForSelector('/html/body/main/nav[2]/div[3]/div/h2[2]', { state: 'visible' });
  }

  // Assert visibility of h2 element (elementId16)
  async assertVisibleH2ElementId16() {
    await this.page.waitForSelector('/html/body/main/nav[2]/div[3]/div/h2[3]', { state: 'visible' });
  }

  // Assert visibility of h2 element (elementId17)
  async assertVisibleH2ElementId17() {
    await this.page.waitForSelector('/html/body/main/nav[2]/div[3]/div/h2[4]', { state: 'visible' });
  }

  // Assert visibility of h2 element (elementId18)
  async assertVisibleH2ElementId18() {
    await this.page.waitForSelector('/html/body/main/nav[2]/div[3]/div/h2[5]', { state: 'visible' });
  }

  // Assert visibility of "We owe you an explanation."
  async assertVisibleExplanationElementId19() {
    await this.page.waitForSelector('h3', { state: 'visible' });
  }

  // Assert visibility of "There are no small contributions: every edit count"
  async assertVisibleContributionsElementId20() {
    await this.page.waitForSelector('text="There are no small contributions: every edit count"', { state: 'visible' });
  }

  // Assert visibility of "Download Wikipedia for Android or iOS"
  async assertVisibleDownloadWikipediaElementId21() {
    await this.page.waitForSelector('text="Download Wikipedia for Android or iOS"', { state: 'visible' });
  }
}

module.exports = GeneratedPageHelpers;