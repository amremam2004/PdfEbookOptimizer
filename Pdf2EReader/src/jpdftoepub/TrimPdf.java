package jpdftoepub;
/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */


import com.itextpdf.text.Document;
import com.itextpdf.text.DocumentException;
import com.itextpdf.text.Rectangle;
import com.itextpdf.text.pdf.PdfArray;
import com.itextpdf.text.pdf.PdfContentByte;
import com.itextpdf.text.pdf.PdfCopy;
import com.itextpdf.text.pdf.PdfDictionary;
import com.itextpdf.text.pdf.PdfImportedPage;
import com.itextpdf.text.pdf.PdfName;
import com.itextpdf.text.pdf.PdfNumber;
import com.itextpdf.text.pdf.PdfReader;
import com.itextpdf.text.pdf.PdfSmartCopy;
import com.itextpdf.text.pdf.PdfStamper;
import com.itextpdf.text.pdf.PdfWriter;
import com.itextpdf.text.pdf.PdfPage;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.FileReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.RandomAccessFile;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.logging.Level;
import java.util.logging.Logger;
//import com.oracle.json.Json;
import org.json.JSONArray;
import org.json.JSONObject;
import org.json.JSONTokener;
import java.nio.file.*;
import org.json.JSONException;

/**
 *
 * @author aemam
 */
class PageInfo {

    public double[] box = null; //[30.8067, 311.58675679999993, 471.88206639999987, 627.0499664],
    public double scale; //" : 3.26474818068643,
    int idx; //" : 0,
    public double W; //" : 1440.0,
    public double[] ctm = null;//" : [0.0, 3.26474818068643, -3.26474818068643, 0.0, 2047.160237003887, -100.57611777795263],
    public int opageno;//" : 39,
    public double H;//" : 1080.0,
    public boolean rotated;//" : true,
    public int inpageno;//" : 20
    public int streamoff = 0;
    public int streamlen = 0;
}

public class TrimPdf {

    public static void main(String[] argv) throws IOException, DocumentException {
        String pages = "";
        String inFile = null;
        String outFile = null;
        String jsonFile = null;
        String streamsFile = null;
        int argidx = 0;
        if (argidx >= argv.length) {
            System.out.println("Please provide arguments");
            return;
        }
        String cmd = argv[argidx++];
        switch (cmd.toLowerCase()) {
            case "decrypt":
            case "uncompress":
            case "compress":
            case "pages":
            case "trim":
            case "maximize":
            case "margins":
            
                if (argidx >= argv.length) {
                    System.out.println("missing input filiename");
                    return;
                }
                inFile = argv[argidx++];
                if(cmd.equals("trim")){
                    if (argidx >= argv.length) {
                            outFile = inFile.replace(".pdf", "-trimmed.pdf");
                    } else {
                        outFile = argv[argidx++];
                    }
                    if (argidx >= argv.length) {
                            jsonFile = inFile + ".trim.json";
                    } else {
                        jsonFile = argv[argidx++];
                    }
                    if (argidx >= argv.length) {
                            streamsFile = inFile + ".streams";
                    } else {
                        streamsFile = argv[argidx++];
                    }
                }
                else{
                    if (argidx >= argv.length) {
                            outFile = inFile.replace(".pdf", String.format("-%s.pdf", cmd));
                    }
                    else{
                    	outFile = argv[argidx++];
                    }
                }
                if ("decrypt".equals(cmd)) {
                    decryptPdf(inFile, outFile);
                } 
                else if("maximize".equals(cmd)){
                	maximize(inFile,outFile);
                }
                else if("margins".equals(cmd)){
                	margins(inFile, outFile);
                }
                else if ("uncompress".equals(cmd)) {
                    UncompressPdf(inFile, outFile);
                } else if ("compress".equals(cmd)) {
                    compressPdf(inFile, outFile);
                } else if ("trim".equals(cmd)) {
                    trimPdf(inFile, outFile, jsonFile, streamsFile);
                } else if ("pages".equals(cmd)) {
                    if (argidx >= argv.length) {
                        pages = "1-1000";
                    } else {
                        pages = argv[argidx++];
                    }
                    selectPages(inFile, outFile, pages);
                }
                break;
            case "crop":
                if (argidx >= argv.length) {
                    System.out.println("Missing input filename");
                    return;
                }
                inFile = argv[argidx++];
                if (argidx >= argv.length) {
                    outFile = inFile.replace(".pdf", String.format("-%s.pdf", "out"));
                } else {
                    outFile = argv[argidx++];
                }
                if (argidx >= argv.length) {
                    jsonFile = inFile + ".json";
                } else {
                    jsonFile = argv[argidx++];
                }
                if (argidx >= argv.length) {
                    streamsFile = inFile + ".cropped-streams";
                } else {
                    streamsFile = argv[argidx++];
                }
                 System.out.print("cropping file\n");
                cropPdf(inFile, outFile, jsonFile, streamsFile);
                break;
        }
    }
    public static PdfArray getBox(PdfDictionary pdfDictionary, PdfName objName) {
    	return pdfDictionary.getAsArray(objName);
    	/*Rectangle media=null;
        if(mediaA!=null)
        	media= new Rectangle(mediaA.getAsNumber(0).floatValue(), (float)mediaA.getAsNumber(1).floatValue(),
        			mediaA.getAsNumber(2).floatValue() - mediaA.getAsNumber(0).floatValue(), 
        			mediaA.getAsNumber(3).floatValue() - mediaA.getAsNumber(1).floatValue());
        return media;*/
    }
    public static String maximize(String pdfFilePath, String pdfOutFile) throws DocumentException, IOException {
    PdfReader reader = new PdfReader(pdfFilePath);
    try {
    	PdfArray[] R = new PdfArray[5];
        PdfStamper stamper = new PdfStamper(reader, new FileOutputStream(pdfOutFile));
        try {
            for (int i = 1; i <= reader.getNumberOfPages(); i++) {
                PdfDictionary pdfDictionary = reader.getPageN(i);
                PdfArray cropArray = new PdfArray();
                Rectangle cropbox = reader.getCropBox(i);  
                Rectangle mediabox = reader.getPageSize(i);
                
                R[0] = getBox(pdfDictionary, PdfName.MEDIABOX);
                R[1] = getBox(pdfDictionary,PdfName.CROPBOX);
                R[2] = getBox(pdfDictionary,PdfName.BLEEDBOX);
                R[3] = getBox(pdfDictionary,PdfName.TRIMBOX);
                R[4] = getBox(pdfDictionary,PdfName.ARTBOX);
                float [] b = new float[]{100000,100000,-100000,-100000};
                for(int i1=0;i1<4;i1++){
                	for(int j1=0;j1<5;j1++){
                		if(R[j1]==null)
                			continue;
                		if(i1<2)
                			b[i1]=Math.min(b[i1], R[j1].getAsNumber(i1).floatValue());
                		else
                			b[i1]=Math.max(b[i1], R[j1].getAsNumber(i1).floatValue());
                		
                	}
                }
                Rectangle newBox = new Rectangle(10,10);
                newBox.setLeft(Math.min(cropbox.getLeft(), mediabox.getLeft()));
                newBox.setRight(Math.max(cropbox.getRight(), mediabox.getRight()));
                newBox.setBottom(Math.min(cropbox.getBottom(), mediabox.getBottom()));
                newBox.setTop(Math.max(cropbox.getTop(), mediabox.getTop()));
                /*b[0]-=10;
                b[1]-=10;
                b[2]+=10;
                b[3]+=10;*/
                cropArray.add(new PdfNumber(b[0]));
                cropArray.add(new PdfNumber(b[1]));
                cropArray.add(new PdfNumber(b[2]));
                cropArray.add(new PdfNumber(b[3]));
                pdfDictionary.put(PdfName.CROPBOX, cropArray);
                pdfDictionary.put(PdfName.MEDIABOX, cropArray);
                pdfDictionary.put(PdfName.TRIMBOX, cropArray);
                pdfDictionary.put(PdfName.BLEEDBOX, cropArray);
                pdfDictionary.put(PdfName.ARTBOX, cropArray);
            }
        } catch(Exception e){
        	e.printStackTrace();
        } finally {
            stamper.close();
        }
    } finally {
        reader.close();
    }
    return pdfOutFile;
}
    
    public static String margins(String pdfFilePath, String pdfOutFile) throws DocumentException, IOException {
    PdfReader reader = new PdfReader(pdfFilePath);
    try {
        PdfStamper stamper = new PdfStamper(reader, new FileOutputStream(pdfOutFile));
        try {
            for (int i = 1; i <= reader.getNumberOfPages(); i++) {
                PdfDictionary pdfDictionary = reader.getPageN(i);
                PdfArray cropArray = new PdfArray();
                Rectangle cropbox = reader.getCropBox(i);  
                Rectangle mediabox = reader.getPageSize(i);
                Rectangle newBox = new Rectangle(10,10);
                newBox.setLeft(Math.max(cropbox.getLeft(), mediabox.getLeft()));
                newBox.setRight(Math.min(cropbox.getRight(), mediabox.getRight()));
                newBox.setBottom(Math.max(cropbox.getBottom(), mediabox.getBottom()));
                newBox.setTop(Math.min(cropbox.getTop(), mediabox.getTop()));
                cropArray.add(new PdfNumber(newBox.getLeft()));
                cropArray.add(new PdfNumber(newBox.getBottom()));
                cropArray.add(new PdfNumber(newBox.getRight()));
                cropArray.add(new PdfNumber(newBox.getTop()));
                pdfDictionary.put(PdfName.CROPBOX, cropArray);
                pdfDictionary.put(PdfName.MEDIABOX, cropArray);
                pdfDictionary.put(PdfName.TRIMBOX, cropArray);
                pdfDictionary.put(PdfName.BLEEDBOX, cropArray);
            }
        } finally {
            stamper.close();
        }
    } finally {
        reader.close();
    }
    return pdfOutFile;
}
    public static String changeSize(String pdfFilePath, int size) throws DocumentException, IOException {
    String filename = pdfFilePath.replace(".pdf","-resized.pdf");
    PdfReader reader = new PdfReader(pdfFilePath);
    try {
        PdfStamper stamper = new PdfStamper(reader, new FileOutputStream(filename));
        try {
            for (int i = 1; i <= reader.getNumberOfPages(); i++) {
                PdfDictionary pdfDictionary = reader.getPageN(i);
                PdfArray cropArray = new PdfArray();
                Rectangle cropbox = reader.getCropBox(i);                   
                cropArray.add(new PdfNumber(cropbox.getLeft()/*-size*/));
                cropArray.add(new PdfNumber(cropbox.getBottom()/*-size*/));
                cropArray.add(new PdfNumber(cropbox.getLeft() + cropbox.getWidth()/*+size*/));
                cropArray.add(new PdfNumber(cropbox.getBottom() + cropbox.getHeight()+size));
                pdfDictionary.put(PdfName.CROPBOX, cropArray);
                pdfDictionary.put(PdfName.MEDIABOX, cropArray);
                pdfDictionary.put(PdfName.TRIMBOX, cropArray);
                pdfDictionary.put(PdfName.BLEEDBOX, cropArray);
            }
            return filename;
        } finally {
            stamper.close();
        }
    } finally {
        reader.close();
    }
}
    public static ArrayList<int[]> getPdfStreams(String json) {
        JSONTokener tokener = null;
        try {
            tokener = new JSONTokener(new FileReader(json));
        } catch (FileNotFoundException e) {
            System.err.format("File Not Found: %s\n", json);
            return null;
        }
        JSONObject jsonData = new JSONObject(tokener);
        JSONArray streams = jsonData.getJSONArray("streams");

        ArrayList<int[]> streamsArray = new ArrayList<>();
        //ArrayList<JSONObject> scalesArray = new ArrayList<>();

        for (int i = 0; i < streams.length(); i++) {
            JSONArray stream = null;
            try {
                stream = streams.getJSONArray(i);
            } catch (JSONException e) {
                e.printStackTrace();
            }
            streamsArray.add(new int[]{stream.getInt(0), stream.getInt(1),stream.getInt(2)});
        }
        return streamsArray;

    }

    public static void trimPdf(String inFile, String outFile, String jsonFile, String streamsFile) throws IOException, DocumentException{
        ArrayList<int[]> streams = getPdfStreams(jsonFile);
        PdfReader reader = new PdfReader(inFile);
        RandomAccessFile fstream = new RandomAccessFile(streamsFile, "r");
        //Rectangle rc;
        Document document = new Document();
        FileOutputStream fOut = new FileOutputStream( outFile);

        PdfCopy pdfCopy = new PdfCopy(document, fOut);

        metaInfo = reader.getInfo();
        ///File resultFile = File.createTempFile("cropped", ".pdf");
        //PdfWriter writer = PdfWriter.getInstance(document, new FileOutputStream(outFile));

        document.open();
        //PdfContentByte cb = writer.getDirectContent();
        PdfImportedPage page = null;
        byte[] data=null;
        for (int[] stream : streams) {
            int pageno = stream[0]+1;
            int len = stream[2];
            int offset = stream[1];
            fstream.seek(offset);
            data = new byte[len];
            fstream.read(data, 0, len);
            reader.setPageContent(pageno, data);
            page = pdfCopy.getImportedPage(reader, pageno);
            pdfCopy.addPage(page);
            
        }
        document.close();
        pdfCopy.close();
        reader.close();
        fstream.close();
        fOut.close();
        
    }
    
    
    public static void decryptPdf(String src, String dest) throws IOException, DocumentException {
        PdfReader reader = new PdfReader(src, "amr".getBytes());

        PdfStamper stamper = new PdfStamper(reader, new FileOutputStream(dest));
        stamper.setEncryption(null, "amr".getBytes(),
                PdfWriter.ALLOW_PRINTING | PdfWriter.ALLOW_COPY, PdfWriter.STANDARD_ENCRYPTION_40 | PdfWriter.DO_NOT_ENCRYPT_METADATA);

        /*int total = reader.getNumberOfPages() + 1; 
         for (int i = 1; i < total; i++) { 
         reader.setPageContent(i, reader.getPageContent(i)); 
         } 
         stamper.close(); 
         */
        stamper.close();
        reader.close();

    }

    public static void UncompressPdf(String src, String dest)
            throws IOException, DocumentException {
        PdfReader reader = new PdfReader(src);

        PdfStamper stamper = new PdfStamper(reader, new FileOutputStream(dest));
        /*stamper.setEncryption(null, "amr".getBytes(),
         PdfWriter.ALLOW_PRINTING |PdfWriter.ALLOW_COPY, PdfWriter.STANDARD_ENCRYPTION_40 | PdfWriter.DO_NOT_ENCRYPT_METADATA);
         */
        boolean comp = Document.compress;
        Document.compress = false;
        /*int total = reader.getNumberOfPages() + 1; 
         for (int i = 1; i < total; i++) { 
         reader.setPageContent(i, reader.getPageContent(i)); 
         } 
         stamper.close(); 
         */
        stamper.close();
        reader.close();
        Document.compress = comp;

    }

    public static void compressPdf(String src, String dest)
            throws IOException, DocumentException {
        PdfReader reader = new PdfReader(src);

        PdfStamper stamper = new PdfStamper(reader, new FileOutputStream(dest));
        stamper.setFullCompression();
        stamper.close();
        reader.close();

    }

    public static void selectPages(String src, String dest, String pages)
            throws IOException, DocumentException {
        PdfReader reader = new PdfReader(src);
        if (pages.length() == 0) {
            reader.selectPages("0-750");
        }
        PdfStamper stamper = new PdfStamper(reader, new FileOutputStream(dest));
        /*stamper.setEncryption(null, "amr".getBytes(),
         PdfWriter.ALLOW_PRINTING |PdfWriter.ALLOW_COPY, PdfWriter.STANDARD_ENCRYPTION_40 | PdfWriter.DO_NOT_ENCRYPT_METADATA);
         */
        stamper.close();
        reader.close();
    }

    public static ArrayList<PageInfo> getPdfCrops(String json) {
        JSONTokener tokener = null;
        try {
            tokener = new JSONTokener(new FileReader(json));
        } catch (FileNotFoundException e) {
            System.err.format("File Not Found: %s\n", json);
            return null;
        }
        JSONObject jsonData = new JSONObject(tokener);
        //JSONObject args = jsonData.getJSONObject("args");
        //JSONArray coords1 = jsonData.getJSONArray("pagesCoords");
        JSONArray scales = jsonData.getJSONArray("scales");

        ArrayList<PageInfo> coordsArray = new ArrayList<>();
        //ArrayList<JSONObject> scalesArray = new ArrayList<>();

        for (int i = 0; i < scales.length(); i++) {
            JSONObject obj = null;
            try {
                obj = scales.getJSONObject(i);
            } catch (JSONException e) {
                e.printStackTrace();
            }

            PageInfo info = new PageInfo();
            info.H = obj.getDouble("H");
            info.W = obj.getDouble("H");
            JSONArray box = obj.getJSONArray("box");
            JSONArray ctm = obj.getJSONArray("ctm");
            info.box = new double[]{box.getDouble(0), box.getDouble(1), box.getDouble(2), box.getDouble(3)};
            info.ctm = new double[]{
                ctm.getDouble(0), ctm.getDouble(1), ctm.getDouble(2),
                ctm.getDouble(3), ctm.getDouble(4), ctm.getDouble(5)};
            info.idx = obj.getInt("idx");
            info.inpageno = obj.getInt("inpageno");;
            info.opageno = obj.getInt("opageno");;
            info.rotated = obj.getBoolean("rotated");
            info.scale = obj.getDouble("scale");
            info.streamoff = obj.getInt("streamoff");
            info.streamlen = obj.getInt("streamlen");
            coordsArray.add(info);
        }
        return coordsArray;

    }
    static HashMap<String, String> metaInfo = null;

    public static void cropPdf(String src, String dst, String json, String streams) throws IOException, DocumentException {
        ArrayList<PageInfo> cropJob = getPdfCrops(json);
        if (cropJob == null) {
            return;
        }
        //String tmpFile = copyToMultiplePages(src, cropJob);
        //trimPdf(src, dst, cropJob);
        copyAllScaled(src, dst, streams, cropJob);
    }

    private static void copyAllPages(String inFile, String outFile)
            throws IOException, DocumentException {

        PdfReader reader = new PdfReader(inFile);
        Document document = new Document();
        metaInfo = reader.getInfo();
        //File resultFile = File.createTempFile("cropped", ".pdf");
        FileOutputStream fOut = new FileOutputStream(
                outFile);
        PdfSmartCopy pdfCopy = new PdfSmartCopy(document, fOut);
        document.open();
        PdfImportedPage page;
        int totalPages = reader.getNumberOfPages();
        for (int pageNumber = 1; pageNumber <= totalPages; pageNumber++) {
            page = pdfCopy.getImportedPage(reader, pageNumber);
            //page.concatCTM(null);
            pdfCopy.addPage(page);
        }

        
        
        document.close();
        pdfCopy.close();
        reader.close();
        fOut.close();
    }
    public static void trimPdf(String inFile, String outFile, ArrayList<PageInfo> cropJob) throws IOException, DocumentException{
        
        PdfReader[] readers = new PdfReader[4];
        for(int i=0;i<4; i++)
            readers[i] = new PdfReader(inFile);
        RandomAccessFile fstream = new RandomAccessFile(inFile + ".cropped-streams", "r");
        Document document = new Document();//new Rectangle(0, 0, 1080, 1440), 0.0f, 0.0f, 0.0f, 0.0f);
        FileOutputStream fOut = new FileOutputStream( outFile);


        metaInfo = readers[0].getInfo();
        PdfCopy pdfCopy = new PdfCopy(document, fOut);

        document.open();
        PdfImportedPage page = null;
        byte[] data=null;
        int i=0; int prevPage=-1;
        for(PageInfo pageInfo: cropJob){
            if(pageInfo.inpageno != prevPage){
                prevPage= pageInfo.inpageno;
                i=0;
            }
            fstream.seek(pageInfo.streamoff);
            data = new byte[pageInfo.streamlen];
            fstream.read(data, 0, pageInfo.streamlen);
            readers[i].setPageContent(pageInfo.inpageno + 1 /*pageInfo.opageno + 1*/, data);
            page = pdfCopy.getImportedPage(readers[i], pageInfo.inpageno+1);
            //page = pdfCopy.getImportedPage(reader, i /*pageInfo.opageno + 1*/);
            //pdfCopy.addPage(page);
            pdfCopy.addPage(page);
            i++;
        }
        document.close();
        pdfCopy.close();
        fOut.close();
        for(i=0;i< 4; i++)
            readers[i].close();
        fstream.close();
        
    }

    private static void copyAllScaled(String inFile, String outFile, String streams,  ArrayList<PageInfo> cropJob)
            throws IOException, DocumentException {

        PdfReader[] readers = new PdfReader[4];
        for(int i=0;i<4; i++)
            readers[i] = new PdfReader(inFile);

        RandomAccessFile fstream = new RandomAccessFile(streams, "r");
       //Rectangle rc;
        Document document = new Document(new Rectangle(0, 0, 1080, 1440), 0.0f, 0.0f, 0.0f, 0.0f);
        metaInfo = readers[0].getInfo();
        ///File resultFile = File.createTempFile("cropped", ".pdf");
        PdfWriter writer = PdfWriter.getInstance(document, new FileOutputStream(outFile));

        document.open();
        PdfContentByte cb = writer.getDirectContent();
        PdfImportedPage page = null;
        byte[] data=null;
        int i=0; int prevPage=-1;
        for (PageInfo pageInfo : cropJob) {
            if(pageInfo.inpageno != prevPage){
                prevPage= pageInfo.inpageno;
                i=0;
            }
            document.newPage();
            fstream.seek(pageInfo.streamoff);
            data = new byte[pageInfo.streamlen];
            fstream.read(data, 0, pageInfo.streamlen);
            readers[i].setPageContent(pageInfo.inpageno + 1, data);
            
            page = writer.getImportedPage(readers[i], pageInfo.inpageno + 1);

                cb.addTemplate(page,
                    (float) pageInfo.ctm[0], (float) pageInfo.ctm[1], (float) pageInfo.ctm[2],
                    (float) pageInfo.ctm[3], (float) pageInfo.ctm[4], (float) pageInfo.ctm[5]);
            i++;
        }

        document.close();
        writer.close();
        for(i=0;i< 4; i++)
            readers[i].close();
        fstream.close();
        //		return resultFile;
    }

    private static String copyToMultiplePages(String inFile, ArrayList<PageInfo> cropJob)
            throws IOException, DocumentException {

        PdfReader reader = new PdfReader(inFile);
        Document document = new Document();
        metaInfo = reader.getInfo();
        String resultFile = inFile.replace(".pdf", "-tmp.pdf");
        PdfCopy pdfCopy = new PdfCopy(document, new FileOutputStream(
                resultFile));
        document.open();
        PdfImportedPage page;

        for (PageInfo pageInfo : cropJob) {
            page = pdfCopy.getImportedPage(reader, pageInfo.inpageno + 1);
            pdfCopy.addPage(page);
        }
        document.close();
        pdfCopy.close();
        reader.close();
        return resultFile;
    }

    private static void cropMultipliedFile(File tmpFile, String dest, ArrayList<PageInfo> cropJob)
            throws FileNotFoundException, DocumentException, IOException {

        PdfReader reader = new PdfReader(tmpFile.getAbsolutePath());

        PdfDictionary pageDict;
        for (PageInfo pageInfo : cropJob) {
            int newPageNumber = pageInfo.opageno + 1;

            pageDict = reader.getPageN(pageInfo.opageno + 1);

            PdfArray scaleBoxArray = new PdfArray();
            scaleBoxArray.add(new PdfNumber(0));
            scaleBoxArray.add(new PdfNumber(0));
            scaleBoxArray.add(new PdfNumber(pageInfo.H));
            scaleBoxArray.add(new PdfNumber(pageInfo.W));

            pageDict.put(PdfName.CROPBOX, scaleBoxArray);
            pageDict.put(PdfName.MEDIABOX, scaleBoxArray);


        }

        PdfStamper stamper = new PdfStamper(reader, new FileOutputStream(
                dest));

        stamper.setMoreInfo(metaInfo);
        stamper.close();
        reader.close();
    }

}
