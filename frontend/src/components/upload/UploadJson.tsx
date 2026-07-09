import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { ArrowLeft, UploadCloud } from "lucide-react";
import { useDropzone, DropzoneOptions } from "react-dropzone";

interface UploadJsonProps {
  onBack: () => void;
  onDrop: DropzoneOptions['onDrop'];
}

export function UploadJson({ onBack, onDrop }: UploadJsonProps) {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/json': ['.json'] },
    maxFiles: 1
  });

  return (
    <div className="flex flex-col gap-8 max-w-2xl mx-auto w-full mt-12">
      <Button variant="ghost" className="w-fit -ml-4" onClick={onBack}>
        <ArrowLeft className="w-4 h-4 mr-2" /> Back to Options
      </Button>
      <Card className="border-primary/20 shadow-xl">
        <CardHeader className="text-center pb-2">
          <CardTitle className="text-2xl">Upload Semester Profile</CardTitle>
          <CardDescription>Drag and drop your JSON file to instantly restore your dashboard.</CardDescription>
        </CardHeader>
        <CardContent className="p-8">
          <div 
            {...getRootProps()} 
            className={`border-2 border-dashed rounded-xl p-16 flex flex-col items-center justify-center text-center transition-colors cursor-pointer group
              ${isDragActive ? 'border-primary bg-primary/10' : 'border-primary/30 hover:bg-primary/5'}`}
          >
            <input {...getInputProps()} />
            <UploadCloud className={`w-12 h-12 mb-4 transition-colors ${isDragActive ? 'text-primary' : 'text-muted-foreground group-hover:text-primary'}`} />
            <p className="text-lg font-medium">{isDragActive ? "Drop JSON here" : "Click to select or drag and drop"}</p>
            <p className="text-sm text-muted-foreground mt-1">Only .json files are supported</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
