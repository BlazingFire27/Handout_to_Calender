"use client"
import { useState, useCallback, useRef } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { FileJson, FileText, ArrowLeft, UploadCloud, X, CheckCircle2, Loader2 } from "lucide-react";
import { useDropzone } from "react-dropzone";
import { SemesterProfile, CourseData } from "@/types";

export default function Home() {
  const [view, setView] = useState<"options" | "upload-json" | "upload-pdf" | "dashboard">("options");
  const [semesterData, setSemesterData] = useState<SemesterProfile | null>(null);

  // PDF State
  const [pdfFiles, setPdfFiles] = useState<File[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [processStatus, setProcessStatus] = useState("");
  const [fileStatuses, setFileStatuses] = useState<Record<string, string>>({});

  // JSON Dropzone
  const onDropJson = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const json = JSON.parse(e.target?.result as string);
        if (json && json.courses) {
          setSemesterData(json as SemesterProfile);
          setView("dashboard");
        } else {
          alert("Invalid JSON format. Expected SemesterProfile structure.");
        }
      } catch (err) {
        alert("Failed to parse JSON file.");
      }
    };
    reader.readAsText(file);
  }, []);

  const { getRootProps: getJsonRootProps, getInputProps: getJsonInputProps, isDragActive: isJsonDragActive } = useDropzone({
    onDrop: onDropJson,
    accept: { 'application/json': ['.json'] },
    maxFiles: 1
  });

  // PDF Dropzone
  const onDropPdf = useCallback((acceptedFiles: File[]) => {
    setPdfFiles(prev => {
      const newFiles = [...prev, ...acceptedFiles];
      if (newFiles.length > 20) {
        alert("Maximum 20 PDFs allowed. Keeping the first 20.");
        return newFiles.slice(0, 20);
      }
      return newFiles;
    });
  }, []);

  const { getRootProps: getPdfRootProps, getInputProps: getPdfInputProps, isDragActive: isPdfDragActive } = useDropzone({
    onDrop: onDropPdf,
    accept: { 'application/pdf': ['.pdf'] },
    maxFiles: 20
  });

  const removePdf = (index: number) => {
    setPdfFiles(prev => prev.filter((_, i) => i !== index));
  };

  // AbortController ref to cancel ongoing backend processing
  const abortControllerRef = useRef<AbortController | null>(null);

  const handlePdfProcessing = async () => {
    if (pdfFiles.length === 0) return;
    setIsProcessing(true);
    setProgress(0);
    setFileStatuses({});
    setProcessStatus(`Starting parallel queue for ${pdfFiles.length} courses...`);

    abortControllerRef.current = new AbortController();
    const aggregatedCourses: CourseData[] = [];
    
    // Live statistics tracking
    let totalEvents = 0;
    let totalSyllabus = 0;
    let totalRefs = 0;
    
    // Tracking progress per file
    const progressTracker = pdfFiles.map(() => ({ completedPages: 0, totalPages: 1, initialized: false }));

    const updateGlobalProgress = () => {
      let totalP = 0;
      let completedP = 0;
      progressTracker.forEach(t => {
        if (t.initialized) {
          totalP += t.totalPages;
          completedP += t.completedPages;
        } else {
          totalP += 1; // dummy weight until init
        }
      });
      setProgress((completedP / totalP) * 100);
    };

    const processFile = async (file: File, index: number) => {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("date_format", "DMY");

      try {
        const response = await fetch("http://127.0.0.1:8000/generate", {
          method: "POST",
          body: formData,
          signal: abortControllerRef.current?.signal,
        });

        if (!response.body) return;

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split("\n").filter(Boolean);

          for (const line of lines) {
            try {
              const data = JSON.parse(line);
              
              if (data.type === "init") {
                progressTracker[index].totalPages = data.total_pages;
                progressTracker[index].initialized = true;
                updateGlobalProgress();
              } else if (data.type === "progress") {
                setFileStatuses(prev => ({ ...prev, [file.name]: data.message }));
              } else if (data.type === "page_done") {
                progressTracker[index].completedPages++;
                totalEvents += data.events_found || 0;
                totalSyllabus += data.syllabus_found || 0;
                totalRefs += data.refs_found || 0;
                
                setProcessStatus(`Extracted ${totalEvents} exams, ${totalSyllabus} topics, and ${totalRefs} textbooks so far...`);
                updateGlobalProgress();
              } else if (data.type === "done") {
                setFileStatuses(prev => ({ ...prev, [file.name]: "✅ Extraction Complete" }));
                const finalData = data.data;
                const courseTitle = finalData.course_title || file.name;
                finalData.evaluation_scheme.forEach((e: any) => e.course_title = courseTitle);
                finalData.syllabus_topics.forEach((s: any) => s.course_title = courseTitle);
                finalData.references.forEach((r: any) => r.course_title = courseTitle);
                aggregatedCourses.push(finalData);
              }
            } catch (err) {
              // Ignore partial JSON chunks
            }
          }
        }
      } catch (error: any) {
        if (error.name === "AbortError") {
          setFileStatuses(prev => ({ ...prev, [file.name]: "🛑 Cancelled" }));
          console.log(`Aborted processing for ${file.name}`);
        } else {
          setFileStatuses(prev => ({ ...prev, [file.name]: "❌ Error" }));
          console.error(`Error processing ${file.name}:`, error);
        }
      }
    };

    // Parallelize all PDF requests
    await Promise.all(pdfFiles.map((file, i) => processFile(file, i)));

    if (!abortControllerRef.current?.signal.aborted) {
      setProcessStatus("Finalizing dashboard...");
      setSemesterData({ courses: aggregatedCourses });
      setIsProcessing(false);
      setView("dashboard");
    }
  };

  if (view === "options") {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-8 w-full max-w-4xl mx-auto">
        <div className="text-center space-y-4">
          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-primary">
            Welcome to Handout2Calendar
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Instantly extract schedules and syllabi from university PDFs using advanced AI, 
            or restore your dashboard instantly from a previous JSON save.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full mt-8">
          <Card 
            className="hover:border-primary/50 hover:bg-primary/10 dark:hover:bg-primary/20 hover:shadow-2xl hover:-translate-y-1 transition-all duration-300 cursor-pointer flex flex-col justify-center text-center p-6 group h-full"
            onClick={() => setView("upload-json")}
          >
            <CardHeader>
              <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform">
                <FileJson className="w-8 h-8 text-primary" />
              </div>
              <CardTitle className="text-2xl">Restore Dashboard</CardTitle>
              <CardDescription className="text-base mt-2">
                Upload your previously saved <br /> <code className="text-primary">Semester_Profile.json</code>
              </CardDescription>
            </CardHeader>
          </Card>

          <Card 
            className="hover:border-primary/50 hover:bg-primary/10 dark:hover:bg-primary/20 hover:shadow-2xl hover:-translate-y-1 transition-all duration-300 cursor-pointer flex flex-col justify-center text-center p-6 group h-full"
            onClick={() => setView("upload-pdf")}
          >
            <CardHeader>
              <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform">
                <FileText className="w-8 h-8 text-primary" />
              </div>
              <CardTitle className="text-2xl">Process New PDFs</CardTitle>
              <CardDescription className="text-base mt-2">
                Upload course handouts to extract schedules from scratch.
              </CardDescription>
            </CardHeader>
          </Card>
        </div>
      </div>
    );
  }

  if (view === "upload-json") {
    return (
      <div className="flex flex-col gap-8 max-w-2xl mx-auto w-full mt-12">
        <Button variant="ghost" className="w-fit -ml-4" onClick={() => setView("options")}>
          <ArrowLeft className="w-4 h-4 mr-2" /> Back to Options
        </Button>
        <Card className="border-primary/20 shadow-xl">
          <CardHeader className="text-center pb-2">
            <CardTitle className="text-2xl">Upload Semester Profile</CardTitle>
            <CardDescription>Drag and drop your JSON file to instantly restore your dashboard.</CardDescription>
          </CardHeader>
          <CardContent className="p-8">
            <div 
              {...getJsonRootProps()} 
              className={`border-2 border-dashed rounded-xl p-16 flex flex-col items-center justify-center text-center transition-colors cursor-pointer group
                ${isJsonDragActive ? 'border-primary bg-primary/10' : 'border-primary/30 hover:bg-primary/5'}`}
            >
              <input {...getJsonInputProps()} />
              <UploadCloud className={`w-12 h-12 mb-4 transition-colors ${isJsonDragActive ? 'text-primary' : 'text-muted-foreground group-hover:text-primary'}`} />
              <p className="text-lg font-medium">{isJsonDragActive ? "Drop JSON here" : "Click to select or drag and drop"}</p>
              <p className="text-sm text-muted-foreground mt-1">Only .json files are supported</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (view === "upload-pdf") {
    return (
      <div className="flex flex-col gap-8 max-w-3xl mx-auto w-full mt-12 mb-16">
        <Button variant="ghost" className="w-fit -ml-4" onClick={() => {
            setView("options");
            setPdfFiles([]);
        }} disabled={isProcessing}>
          <ArrowLeft className="w-4 h-4 mr-2" /> Back to Options
        </Button>

        <Card className="border-primary/20 shadow-xl">
          <CardHeader className="text-center pb-2">
            <CardTitle className="text-2xl">Process Course Handouts</CardTitle>
            <CardDescription>Upload your PDF handouts to extract schedules, syllabi, and textbooks.</CardDescription>
          </CardHeader>
          <CardContent className="p-8 space-y-6">
            
            {/* Dropzone Area */}
            {!isProcessing && (
              <div 
                {...getPdfRootProps()} 
                className={`border-2 border-dashed rounded-xl p-12 flex flex-col items-center justify-center text-center transition-colors cursor-pointer group
                  ${isPdfDragActive ? 'border-primary bg-primary/10' : 'border-primary/30 hover:bg-primary/5'}`}
              >
                <input {...getPdfInputProps()} />
                <UploadCloud className={`w-12 h-12 mb-4 transition-colors ${isPdfDragActive ? 'text-primary' : 'text-muted-foreground group-hover:text-primary'}`} />
                <p className="text-lg font-medium">{isPdfDragActive ? "Drop PDFs here" : "Click to select or drag and drop"}</p>
                <p className="text-sm text-muted-foreground mt-1">Only .pdf files are supported</p>
                
                <div className="mt-6 bg-amber-500/10 text-amber-600 dark:text-amber-400 px-4 py-2 rounded-md text-sm border border-amber-500/20 max-w-md mx-auto">
                  <strong>Limit:</strong> Max 20 PDFs allowed at once. <br/>
                  <em>(Preferably 15 or less for the fastest processing speed).</em>
                </div>
              </div>
            )}

            {/* File List */}
            {pdfFiles.length > 0 && !isProcessing && (
              <div className="space-y-3">
                <h3 className="font-semibold flex items-center justify-between text-sm">
                  Selected Files ({pdfFiles.length}/20)
                  <Button variant="ghost" size="sm" onClick={() => setPdfFiles([])} className="h-8 px-2 text-destructive hover:text-destructive hover:bg-destructive/10">Clear All</Button>
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-60 overflow-y-auto p-1 pr-2">
                  {pdfFiles.map((file, i) => (
                    <div key={i} className="flex items-center justify-between bg-muted/50 border rounded-md p-2 pl-3">
                      <span className="text-sm truncate mr-2" title={file.name}>{file.name}</span>
                      <Button variant="ghost" size="icon" className="h-6 w-6 text-muted-foreground hover:text-destructive shrink-0" onClick={() => removePdf(i)}>
                        <X className="w-4 h-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Processing State */}
            {isProcessing && (
              <div className="py-8 space-y-6">
                <div className="flex flex-col items-center justify-center text-center space-y-4">
                  <div className="relative w-16 h-16">
                    <Loader2 className="w-16 h-16 text-primary animate-spin" />
                    <div className="absolute inset-0 flex items-center justify-center text-xs font-bold text-primary">
                      {Math.round(progress)}%
                    </div>
                  </div>
                  <div>
                    <h3 className="text-xl font-semibold">AI is analyzing your handouts</h3>
                    <p className="text-muted-foreground mt-1">{processStatus}</p>
                  </div>
                </div>
                <Progress value={progress} className="w-full h-3" />
                
                {Object.keys(fileStatuses).length > 0 && (
                  <div className="bg-muted/10 border rounded-lg p-3 space-y-1.5 max-h-40 overflow-y-auto">
                    {Object.entries(fileStatuses).map(([name, status]) => (
                      <div key={name} className="flex justify-between items-center text-xs border-b border-muted/50 last:border-0 pb-1.5 last:pb-0">
                        <span className="font-medium truncate mr-4 text-primary max-w-[60%]">{name}</span>
                        <span className={`truncate font-medium ${status.includes('✅') ? 'text-green-500' : status.includes('❌') ? 'text-destructive' : 'text-muted-foreground'}`}>{status}</span>
                      </div>
                    ))}
                  </div>
                )}
                
                <div className="bg-primary/5 border border-primary/20 rounded-lg p-4 mt-6">
                  <h4 className="font-semibold text-sm mb-2 flex items-center">
                    <CheckCircle2 className="w-4 h-4 mr-2 text-primary" /> Why does this take time?
                  </h4>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    The AI physically reads every page of your PDF, understands the grading scheme, reformats all exam dates into strict formats, and compiles textbooks into a structured JSON payload. We process them one by one to ensure zero data corruption. (Note: AIGateway processing may take up to 60 seconds per page).
                  </p>
                </div>
                <div className="flex justify-center mt-4">
                  <Button variant="outline" className="text-destructive hover:bg-destructive/10 hover:text-destructive" onClick={() => {
                    abortControllerRef.current?.abort();
                    setIsProcessing(false);
                    setProcessStatus("");
                    setProgress(0);
                  }}>
                    Cancel Processing
                  </Button>
                </div>
              </div>
            )}

            {!isProcessing && (
              <Button 
                className="w-full" 
                size="lg" 
                disabled={pdfFiles.length === 0}
                onClick={handlePdfProcessing}
              >
                Extract Data via AI
              </Button>
            )}

          </CardContent>
        </Card>
      </div>
    );
  }

  // Temporary Dashboard Fallback
  if (view === "dashboard") {
    return (
      <div className="flex flex-col gap-6 max-w-5xl mx-auto w-full pb-16">
        <div className="flex items-center justify-between border-b pb-4">
          <h1 className="text-3xl font-bold tracking-tight">Your Semester Dashboard</h1>
          <Button variant="outline" onClick={() => {
            setView("options");
            setPdfFiles([]);
            setSemesterData(null);
          }}>Upload More</Button>
        </div>
        
        <div className="bg-card border rounded-xl p-6 shadow-sm overflow-auto max-h-[70vh]">
          <h2 className="text-xl font-semibold mb-4 text-primary">Raw Aggregated Data</h2>
          <p className="text-sm text-muted-foreground mb-4">This perfectly formatted JSON data represents the combined output of all uploaded PDFs. In the next phase, this will be rendered into a beautiful UI.</p>
          <pre className="text-sm font-mono text-foreground/80 whitespace-pre-wrap break-words">
            {JSON.stringify(semesterData, null, 2)}
          </pre>
        </div>
      </div>
    );
  }

  return null;
}
