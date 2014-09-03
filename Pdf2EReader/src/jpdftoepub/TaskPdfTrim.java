package jpdftoepub;

import java.awt.Desktop;
import java.awt.Rectangle;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.Map.Entry;
import java.util.concurrent.ExecutionException;

import javax.swing.JOptionPane;
import javax.swing.ProgressMonitor;
import javax.swing.SwingWorker;

import bd.amazed.pdfscissors.model.PageRectsMap;
import bd.amazed.pdfscissors.model.PdfFile;





import java.util.regex.*;
public class TaskPdfTrim extends SwingWorker<Boolean, Void> {

	private PdfFile pdfFile;
	private File targetFile;
	PageRectsMap pageRectsMap;
	private int splits;
	private int viewWidth;
	private int viewHeight;
	private int W, H;
	private String pageRange = "";
	private boolean includeArea = true;
	ProgressMonitor progressMonitor;
	public void setPageRange(String pages) {this.pageRange = pages;};
	public void setPageDimensions(int W, int H) {this.H = H; this.W = W;}
	public void setIncludeArea(boolean include) { this.includeArea = include;}
	public TaskPdfTrim(PdfFile pdfFile, File targetFile, int splits,  PageRectsMap pageRectsMap, int viewWidth, int viewHeight,
			ProgressMonitor progressMonitor, int pageCount) {
		this.pdfFile = pdfFile;
		this.targetFile = targetFile;
		this.pageRectsMap = pageRectsMap;
		this.splits = splits;
		this.viewWidth = viewWidth;
		this.viewHeight = viewHeight;
		this.progressMonitor = progressMonitor;
	}

	@Override
	protected Boolean doInBackground() throws Exception {
		debug("Trimming to " + targetFile + "...");
		float pdfWidth = pdfFile.getNormalizedPdfWidth();
		float pdfHeight = pdfFile.getNormalizedPdfHeight();
		//HashMap<Integer, ArrayList<Rectangle>>
		HashMap<Integer, ArrayList<Rectangle>> rectMap = pageRectsMap.getHashMap();
		ArrayList<Rectangle> trimRects = null;
		Rectangle rdefault = null;
		FileWriter pageRects = new FileWriter(targetFile + ".pagerects");
		pageRects.write("{");
		Iterator<Entry<Integer, ArrayList<Rectangle>>> it = rectMap.entrySet().iterator();

		int pageIdx = 0;
		while(it.hasNext())
		{
			Entry<Integer, ArrayList<Rectangle>> entry = it.next();
			int pageno = entry.getKey();
			trimRects = pageRectsMap.getConvertedRectsForCropping(pageno, viewWidth, viewHeight, pdfWidth, pdfHeight);
			int rectIdx = 0;
			String sline = String.format(
					"%s%d:[",
					pageIdx==0?"":", ",
					pageno-1);
			for(Rectangle rc: trimRects){
				if(pageIdx==0 && rectIdx == 0)
				{
					rdefault = rc;
				}
				sline += String.format(
						"%s(%d,%d,%d,%d)",
						rectIdx==0?"":", ",
						 rc.x, rc.y,(rc.x+rc.width), (rc.y + rc.height));
				rectIdx ++;
				
			}
			sline+="]";
			pageRects.write(sline);
			pageIdx++;
		}
		pageRects.write("}");
		pageRects.close();

		String[] args = new String[]{
				getPythonExe(),
				"-u",
				System.getProperty("user.dir") + System.getProperty("file.separator") + "pyPdfMiner.zip",
				"-S", String.format("%d", this.splits),
				"-W", String.format("%d", this.W),
				"-H", String.format("%d", this.H),
				"-o", targetFile.getAbsolutePath()
				};
				ArrayList<String> lstArgs = new ArrayList<String>(Arrays.asList(args));
				if(this.pageRange != null && this.pageRange.trim().length()>0)
				{
					lstArgs.add("-n");
					lstArgs.add(this.pageRange);
				}
				if(rdefault !=null)
				{
					lstArgs.addAll(Arrays.asList(new String[]{
						"-b", String.format("%d",rdefault.x) , String.format("%d",rdefault.y), 
							String.format("%d",(rdefault.x+rdefault.width)) ,
							String.format("%d",(rdefault.y+rdefault.height)),
						"-B", (targetFile + ".pagerects")
					}));
				}
				if(!includeArea){
					lstArgs.add("-x");
				}
				lstArgs.add(pdfFile.getOriginalFile().getAbsolutePath());
				int idx=0;
				System.out.println("");
				for(String s: lstArgs)
				{
					if(idx>0)
						System.out.print(" ");
					if(s.contains(" ")){
						System.out.print("\"" + s + "\"");
					}
					else
						System.out.print(s);
					idx++;
				
				}
				System.out.println("");
				//System.out.println(lstArgs.toString());
				ProcessBuilder pb = new ProcessBuilder(lstArgs.toArray(new String[0]));
				Map<String, String> env = pb.environment();
				env.put("PATH", env.get("PATH") + System.getProperty("path.separator") + System.getProperty("java.home") + System.getProperty("file.separator") +  "bin");
				Process process = pb.start();
				InputStream is = process.getInputStream();
				InputStreamReader isr = new InputStreamReader(is);
				BufferedReader br = new BufferedReader(isr);
				String line;

				//System.out.printf("Output of running %s is:", Arrays.toString(args));

				Pattern p = Pattern.compile("^\\s*([a-z]+\\s*)+(\\d+)\\s*$", Pattern.CASE_INSENSITIVE );

				while ((line = br.readLine()) != null) {
					Matcher m = p.matcher(line);
					if(m.matches())
					{
						int pageNo = Integer.parseInt(m.group(2));
						
						progressMonitor.setProgress(pageNo);
						progressMonitor.setNote(line);
					}
				  System.out.println(line);
				}	
		
		
		debug("Cropping success : " + targetFile);
		return true;
	}

	@Override
	protected void done() {
		super.done();
		progressMonitor.close();
		if (!progressMonitor.isCanceled()) {

			try {
				if (this.get()) {
					if (Desktop.isDesktopSupported()) {
						progressMonitor.setNote("Cropping done!");
						try {
							Desktop.getDesktop().open(targetFile);
						} catch (IOException e) {
							JOptionPane.showMessageDialog(null, "Cropping done.\nFile saved to \n" + targetFile.getAbsolutePath());
						}
					}
				} else {
					throw new ExecutionException("Failed to save!", null); // I guess this will never happen
				}
			} catch (InterruptedException e) {
				e.printStackTrace(); // ignore
			} catch (ExecutionException e) {
				JOptionPane.showMessageDialog(null, "Failed to save image ...\nDetails:" + e.getCause());
				e.printStackTrace();
			}
		}
	}

	private void debug(String string) {
		System.out.println("TaskPdfTrim:" + string);
	}
	
	public static String getPythonExe(){
		String path = System.getenv("PATH");
		String fileSep = System.getProperty("file.separator");
		String pathSep = System.getProperty("path.separator");
		String[] paths = path.split(pathSep);
		String pythonPath=null;

		for(String p: paths){
			File f = new File(p+fileSep + "python.exe");
			if(f.isFile()){
				pythonPath = f.getAbsolutePath();
				break;
			}
		}
		if(pythonPath == null){
			String[] Pythons = {"C:\\python27", "C:\\Python","C:\\Python3","C:\\Python33"};
			for(String p: Pythons){
				File f = new File(p+fileSep + "python.exe");
				if(f.isFile()){
					pythonPath = f.getAbsolutePath();
					break;
				}
			}
		}
		if(pythonPath==null)
			pythonPath = "python.exe";
		return pythonPath;
	}
}
