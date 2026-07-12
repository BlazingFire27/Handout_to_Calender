import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { FileJson, FileText } from "lucide-react";

interface UploadOptionsProps {
  onSelect: (view: "upload-json" | "upload-pdf") => void;
}

export function UploadOptions({ onSelect }: UploadOptionsProps) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] gap-8 w-full max-w-4xl mx-auto">
      <div className="text-center space-y-4 flex flex-col items-center">
        <div className="w-72 md:w-80 aspect-[2.5/1] overflow-hidden rounded-xl border border-border bg-white flex items-center justify-center shadow-md mb-4 shrink-0">
          <img
            src="/logo_512x512.png"
            alt="Handout2Calendar Logo"
            className="w-full h-full object-cover scale-[1.05]"
          />
        </div>
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
          onClick={() => onSelect("upload-json")}
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
          onClick={() => onSelect("upload-pdf")}
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
