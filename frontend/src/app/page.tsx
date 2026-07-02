"use client"
import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { FileJson, FileText, ArrowLeft, UploadCloud } from "lucide-react";

export default function Home() {
  const [view, setView] = useState<"options" | "upload-json" | "upload-pdf" | "dashboard">("options");

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
          {/* Option 1 */}
          <Card 
            className="hover:border-primary/50 hover:shadow-lg transition-all cursor-pointer flex flex-col justify-center text-center p-6 group h-full"
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

          {/* Option 2 */}
          <Card 
            className="hover:border-primary/50 hover:shadow-lg transition-all cursor-pointer flex flex-col justify-center text-center p-6 group h-full"
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
            <div className="border-2 border-dashed border-primary/30 rounded-xl p-16 flex flex-col items-center justify-center text-center hover:bg-primary/5 transition-colors cursor-pointer group">
              <UploadCloud className="w-12 h-12 text-muted-foreground group-hover:text-primary transition-colors mb-4" />
              <p className="text-lg font-medium">Click to select or drag and drop</p>
              <p className="text-sm text-muted-foreground mt-1">Only .json files are supported</p>
            </div>
            <Button className="w-full mt-6" size="lg" disabled>Restore Dashboard</Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (view === "upload-pdf") {
    return (
      <div className="flex flex-col gap-8 max-w-3xl mx-auto w-full mt-12">
        <Button variant="ghost" className="w-fit -ml-4" onClick={() => setView("options")}>
          <ArrowLeft className="w-4 h-4 mr-2" /> Back to Options
        </Button>
        <Card className="border-primary/20 shadow-xl">
          <CardHeader className="text-center pb-2">
            <CardTitle className="text-2xl">Process Course Handouts</CardTitle>
            <CardDescription>Upload your PDF handouts to extract schedules, syllabi, and textbooks.</CardDescription>
          </CardHeader>
          <CardContent className="p-8">
            <div className="border-2 border-dashed border-primary/30 rounded-xl p-16 flex flex-col items-center justify-center text-center hover:bg-primary/5 transition-colors cursor-pointer group">
              <UploadCloud className="w-12 h-12 text-muted-foreground group-hover:text-primary transition-colors mb-4" />
              <p className="text-lg font-medium">Click to select or drag and drop</p>
              <p className="text-sm text-muted-foreground mt-1">Only .pdf files are supported</p>
              
              <div className="mt-6 bg-amber-500/10 text-amber-600 dark:text-amber-400 px-4 py-2 rounded-md text-sm border border-amber-500/20 max-w-md mx-auto">
                <strong>Limit:</strong> Max 20 PDFs allowed at once. <br/>
                <em>(Preferably 15 or less for the fastest processing speed).</em>
              </div>
            </div>
            <Button className="w-full mt-6" size="lg" disabled>Extract Data via AI</Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return null;
}
