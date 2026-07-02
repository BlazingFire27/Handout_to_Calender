import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <div className="flex flex-col gap-8 w-full">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">Upload your university handout or previous Semester_Profile.json.</p>
      </div>
      
      {/* Mobile-first flex-col, Grid on md+ screens */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Upload Zone */}
        <Card className="md:col-span-1">
          <CardHeader>
            <CardTitle>Upload</CardTitle>
            <CardDescription>Drag and drop your PDF here</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <div className="border-2 border-dashed border-border rounded-lg p-12 text-center text-sm text-muted-foreground hover:bg-muted/50 transition-colors cursor-pointer">
              Click to select or drop a file
            </div>
            <Button className="w-full">Process Document</Button>
          </CardContent>
        </Card>

        {/* Results Area */}
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>Extracted Data</CardTitle>
            <CardDescription>Your schedule, syllabus, and books will appear here.</CardDescription>
          </CardHeader>
          <CardContent className="min-h-[300px] flex items-center justify-center text-muted-foreground bg-muted/20 rounded-md border border-dashed">
            No data loaded yet.
          </CardContent>
        </Card>

      </div>
    </div>
  );
}
