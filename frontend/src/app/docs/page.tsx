import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function DocsPage() {
  return (
    <div className="flex flex-col gap-8 max-w-4xl mx-auto w-full">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold tracking-tight">Documentation</h1>
        <p className="text-muted-foreground">Learn how to use Handout2Calendar safely and effectively.</p>
      </div>

      <div className="flex flex-col gap-6">
        <Card>
          <CardHeader>
            <CardTitle>How it Works</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-sm leading-relaxed text-muted-foreground">
            <p>
              Handout2Calendar uses advanced AI to extract your <strong>Evaluation Schedule</strong>, 
              <strong>Syllabus</strong>, and <strong>Textbook References</strong> directly from your university PDF handouts.
            </p>
            <p>
              Once extracted, you can review the data on the dashboard, edit any mistakes, and then 
              download a universal <code>.ics</code> calendar file to import into Google Calendar, Notion, or Outlook.
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>Privacy & Security</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-sm leading-relaxed text-muted-foreground">
            <p>
              This application is completely stateless. <strong>We do not use a database.</strong> Your data is processed 
              in memory on our secure backend and instantly returned to you as a JSON file.
            </p>
            <p>
              To restore your dashboard in the future, simply upload your <code>Semester_Profile.json</code> instead of the PDF.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
