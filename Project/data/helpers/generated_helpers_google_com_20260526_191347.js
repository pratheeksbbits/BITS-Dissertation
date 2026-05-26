class GeneratedPageHelpers {
  constructor(page) {
    this.page = page;
  }

  // element_id=0, tag=div, stable=true
  async waitForDivGeneric() {
    await this.page.waitForSelector(".k1zIA", { state: 'visible' });
  }

  // element_id=1, tag=div, stable=true
  async waitForDivChooseWhat() {
    await this.page.waitForSelector(".C85rO", { state: 'visible' });
  }

}

module.exports = GeneratedPageHelpers;