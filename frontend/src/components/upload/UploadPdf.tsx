import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { ArrowLeft, UploadCloud, X, Loader2, CheckCircle2 } from "lucide-react";
import { useDropzone, DropzoneOptions } from "react-dropzone";

interface UploadPdfProps {
  onBack: () => void;
  onDrop: DropzoneOptions['onDrop'];
  pdfFiles: File[];
  onRemovePdf: (index: number) => void;
  onClearPdfs: () => void;
  isProcessing: boolean;
  progress: number;
  processStatus: string;
  fileStatuses: Record<string, string>;
  onExtract: () => void;
  onCancel: () => void;
}

export function UploadPdf({
  onBack,
  onDrop,
  pdfFiles,
  onRemovePdf,
  onClearPdfs,
  isProcessing,
  progress,
  processStatus,
  fileStatuses,
  onExtract,
  onCancel
}: UploadPdfProps) {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    maxFiles: 20
  });

  return (
    <div className="max-w-6xl mx-auto w-full mt-12 mb-16 px-4">
      <Button variant="ghost" className="w-fit -ml-4 mb-6" onClick={onBack} disabled={isProcessing}>
        <ArrowLeft className="w-4 h-4 mr-2" /> Back to Options
      </Button>

      <div className={pdfFiles.length > 0 ? "flex flex-col md:flex-row gap-8 items-start" : "flex flex-col items-center justify-center"}>
        {/* Left Side: Upload Zone & Extract Button */}
        <div className={pdfFiles.length > 0 ? "w-full md:w-1/2 lg:w-7/12 sticky top-6" : "w-full max-w-2xl"}>
          <Card className="border-primary/20 shadow-xl">
            <CardHeader className="text-center pb-2">
              <CardTitle className="text-2xl">Process Course Handouts</CardTitle>
              <CardDescription>Upload your PDF handouts to extract schedules, syllabi, and textbooks.</CardDescription>
            </CardHeader>
            <CardContent className="p-6 md:p-8 space-y-6">
              
              {/* Dropzone Area */}
              {!isProcessing && (
                <div 
                  {...getRootProps()} 
                  className={`border-2 border-dashed rounded-xl p-8 md:p-12 flex flex-col items-center justify-center text-center transition-colors cursor-pointer group
                    ${isDragActive ? 'border-primary bg-primary/10' : 'border-primary/30 hover:bg-primary/5'}`}
                >
                  <input {...getInputProps()} />
                  <UploadCloud className={`w-12 h-12 mb-4 transition-colors ${isDragActive ? 'text-primary' : 'text-muted-foreground group-hover:text-primary'}`} />
                  <p className="text-lg font-medium">{isDragActive ? "Drop PDFs here" : "Click to select or drag and drop"}</p>
                  <p className="text-sm text-muted-foreground mt-1">Only .pdf files are supported</p>
                  
                  <div className="mt-6 bg-amber-500/10 text-amber-600 dark:text-amber-400 px-4 py-2 rounded-md text-sm border border-amber-500/20 max-w-md mx-auto">
                    <strong>Limit:</strong> Max 20 PDFs allowed at once. <br/>
                    <em>(Preferably 15 or less for the fastest processing speed).</em>
                  </div>
                </div>
              )}

              {/* Processing Header */}
              {isProcessing && (
                <div className="py-6 space-y-6">
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
                  
                  <div className="bg-primary/5 border border-primary/20 rounded-lg p-4 mt-6">
                    <h4 className="font-semibold text-sm mb-2 flex items-center">
                      <CheckCircle2 className="w-4 h-4 mr-2 text-primary" /> Why does this take time?
                    </h4>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      The AI physically reads every page of your PDF, understands the grading scheme, reformats all exam dates into strict formats, and compiles textbooks into a structured JSON payload. We process them safely to ensure zero data corruption.
                    </p>
                  </div>
                  <div className="flex justify-center mt-4">
                    <Button variant="outline" className="text-destructive hover:bg-destructive/10 hover:text-destructive" onClick={onCancel}>
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
                  onClick={onExtract}
                >
                  Extract Data via AI
                </Button>
              )}

            </CardContent>
          </Card>
        </div>

        {/* Right Side: Scrollable Lists Container */}
        {pdfFiles.length > 0 && (
          <div className="w-full md:w-1/2 lg:w-5/12">
            
            {/* File Selection View */}
            {!isProcessing && (
              <Card className="border-primary/20 shadow-md">
                <CardHeader className="pb-3 border-b border-border/50 bg-muted/20">
                  <CardTitle className="text-lg flex items-center justify-between">
                    Selected Files ({pdfFiles.length}/20)
                    <Button variant="ghost" size="sm" onClick={onClearPdfs} className="h-8 px-2 text-destructive hover:text-destructive hover:bg-destructive/10">Clear All</Button>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="max-h-[500px] overflow-y-auto p-4 space-y-3 custom-scrollbar">
                    {pdfFiles.map((file, i) => (
                      <div key={i} className="flex items-center justify-between bg-muted/50 border rounded-md p-3">
                        <span className="text-sm truncate mr-2 font-medium" title={file.name}>{file.name}</span>
                        <Button variant="ghost" size="icon" className="h-6 w-6 text-muted-foreground hover:text-destructive shrink-0" onClick={(e) => { e.stopPropagation(); onRemovePdf(i); }}>
                          <X className="w-4 h-4" />
                        </Button>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Processing Status View */}
            {isProcessing && Object.keys(fileStatuses).length > 0 && (
              <Card className="border-primary/20 shadow-md">
                <CardHeader className="pb-3 border-b border-border/50 bg-muted/20">
                  <CardTitle className="text-lg">Processing Log</CardTitle>
                  <CardDescription>Live updates from the AI Gateway</CardDescription>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="max-h-[500px] overflow-y-auto p-4 space-y-2 custom-scrollbar">
                    {Object.entries(fileStatuses).map(([name, status]) => (
                      <div key={name} className="flex flex-col bg-muted/30 border rounded-md p-3">
                        <span className="font-semibold truncate text-primary text-sm mb-1" title={name}>{name}</span>
                        <span className={`text-xs font-medium ${status.includes('✅') ? 'text-green-500' : status.includes('❌') ? 'text-destructive' : 'text-muted-foreground'}`}>{status}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

          </div>
        )}
      </div>
    </div>
  );
}
