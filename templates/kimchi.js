const widget = new ListWidget()

const indexData = await fetchFngValue()

await createWidget()

// used for debugging if script runs inside the app
if (!config.runsInWidget) {
    await widget.presentSmall()
}

widget.setPadding(10, 10, 10, 10)
widget.url = 'https://alternative.me/crypto/fear-and-greed-index/'

Script.setWidget(widget)
Script.complete()

// build the content of the widget
async function createWidget() {

    let line1, line2, line3
    let icon = widget.addStack()

    const coin = await getImage('bitcoin')
    const coinImg = icon.addImage(coin)
    coinImg.imageSize = new Size(30, 30)

    icon.layoutHorizontally()
    icon.addSpacer(8)

    let iconRow = icon.addStack()
    iconRow.layoutVertically()

    let iconText = iconRow.addStack()
    line1 = iconText.addText("Kimchi")
    line1.font = Font.mediumRoundedSystemFont(25)
    // line1.leftAlignText()

    line2 = widget.addText("by PetaniKimchi.id")
    line2.font = Font.lightRoundedSystemFont(11)
    line2.leftAlignText()

    widget.addSpacer(10)

    let row = widget.addStack()
    row.layoutHorizontally()

    let fngText = row.addText("Margin: ")
    fngText.font = Font.mediumRoundedSystemFont(18)


    let fngValue = row.addText(indexData.value.toString())
    fngValue.textColor = new Color('#' + fngColouring(indexData.value.toString()))
    fngValue.font = Font.regularMonospacedSystemFont(18)

    line3 = widget.addText(indexData.value_classification.toString())
    line3.textColor = new Color('#' + fngColouring(indexData.value.toString()))
    line3.font = Font.regularMonospacedSystemFont(18)

    widget.addSpacer(10)

    let row2 = widget.addStack()
    row2.layoutHorizontally()

    let timeStr = row2.addText('Update in: ')
    timeStr.font = Font.lightRoundedSystemFont(13)

    let relativeDate = toDateTime(indexData.time_until_update)
    let time = row2.addDate(relativeDate)
    time.font = Font.lightMonospacedSystemFont(13)
    time.applyTimerStyle()

}

// Create the datetime object when update will happen
function toDateTime(secs) {
    const t = new Date();

    t.setSeconds(+t.getSeconds() + +secs);
    console.log(t)

    return t;
}

// Get coloring dependant on the fng value
function fngColouring(indexValue) {
    let colorCode = ''
    if (indexValue >= 90) {
        colorCode = '65c64c'
    }
    if (indexValue < 90) {
        colorCode = '79d23c'
    }
    if (indexValue <= 75) {
        colorCode = '9bbe44'
    }
    if (indexValue <= 63) {
        colorCode = 'c6bf22'
    }
    if (indexValue <= 54) {
        colorCode = 'dfce60'
    }
    if (indexValue <= 46) {
        colorCode = 'd8bc59'
    }
    if (indexValue <= 35) {
        colorCode = 'e39d64'
    }
    if (indexValue <= 25) {
        colorCode = 'd17339'
    }
    if (indexValue <= 10) {
        colorCode = 'b74d34'
    }

    return colorCode
}

// fetches the fng value
async function fetchFngValue() {

    let url = 'https://api.alternative.me/fng/'
    const req = new Request(url)
    const apiResult = await req.loadJSON()
    let indexValue = apiResult.data[0]

    return indexValue
}

// get images from local filestore or download them once
async function getImage(image) {
    let fm = FileManager.local()
    let dir = fm.documentsDirectory()
    let path = fm.joinPath(dir, image)
    if (fm.fileExists(path)) {
        return fm.readImage(path)
    } else {
        // download once
        let imageUrl
        switch (image) {
            case 'bitcoin':
                imageUrl = "/images/coin_icons/bitcoin.jpg"
                break
            case 'ripple':
                imageUrl = "/images/coin_icons/ripple.jpg"
                break
            default:
                console.log(`Sorry, couldn't find ${image}.`);
        }
        let iconImage = await loadImage('https://alternative.me' + imageUrl)
        fm.writeImage(path, iconImage)
        return iconImage
    }
}

// helper function to download an image from a given url
async function loadImage(imgUrl) {
    const req = new Request(imgUrl)
    return await req.loadImage()
}

// end of script