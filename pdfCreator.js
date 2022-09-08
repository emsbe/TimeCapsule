import { PDFDocument, StandardFonts } from 'pdf-lib'
//import fs from 'fs'
import fetch from "node-fetch";
import fs from 'fs'
import FileSaver from 'file-saver'
import fontkit from '@pdf-lib/fontkit';


async function createPdf(){

    // These should be Uint8Arrays or ArrayBuffers
// This data can be obtained in a number of different ways
// If your running in a Node environment, you could use fs.readFile()
// In the browser, you could make a fetch() call and use res.arrayBuffer()
    let url = './single_page_3_images.pdf'
/*    const existingPdfBytes = await fetch('./single_page_3_images.pdf').then((res) => res.arrayBuffer)
    var formPdfBytes = new Uint8Array(existingPdfBytes)
    console.log('readFile called')*/



    // Load a PDF with form fields
    const pdfUTF8 = fs.readFileSync(url)
    const pdfDoc = await PDFDocument.load(pdfUTF8)
    pdfDoc.registerFontkit(fontkit);

    url = './images/user_photo.jpeg'
    const uint8Array = fs.readFileSync(url)
    //var imageBytes = new TextEncoder("utf-8").encode(pdfUTF8);
    console.log('readFile called')
    const image3 = await pdfDoc.embedJpg(uint8Array)



// Embed the Mario and emblem images
//   const marioImage = await pdfDoc.embedJpg(imageBytes)

// Get the form containing all the fields
    const form = pdfDoc.getForm()

// Get all fields in the PDF by their names
    const dateField = form.getTextField('Title')
    const messageField = form.getTextField('Message')

    const image1Field = form.getButton('Image1_af_image')
    const image2Field = form.getButton('Image2_af_image')
    const image3Field = form.getButton('Image3_af_image')




// Fill in the basic info fields
    dateField.setText('01-01-2022')
    messageField.setText('Am meisten freue ich mich darauf, Zeit mit Emma zu verbringen und London zu entdecken. Ich gespannt auf die andere Kultur und möchte möglichst viel das Alltagsleben der Briten entdecken')

// Fill the character image field with our Mario image
    image1Field.setImage(image3)
    image2Field.setImage(image3)
    image3Field.setImage(image3)



    const helvetica = await pdfDoc.embedFont(fs.readFileSync('specialFont.otf'))
    messageField.updateAppearances(helvetica)
    form.flatten()


// Serialize the PDFDocument to bytes (a Uint8Array)
    const pdfBytes = await pdfDoc.save()

    fs.writeFileSync('foo.pdf', pdfBytes )
    // const blob = new Blob( [ pdfBytes ], { type: "application/pdf" } );
    // FileSaver.saveAs(blob, 'foo.pdf')
    // download(pdfBytes, "example.pdf", "application/pdf");

// For example, `pdfBytes` can be:
//   • Written to a file in Node
//   • Downloaded from the browser
//   • Rendered in an <iframe>


}


createPdf().catch((err) => console.log(err));