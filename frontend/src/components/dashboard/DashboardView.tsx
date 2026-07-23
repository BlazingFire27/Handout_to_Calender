import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselNext,
  CarouselPrevious,
} from "@/components/ui/carousel";
import { FileJson, UploadCloud, Download, Calendar, ExternalLink, BookOpen } from "lucide-react";
import { SemesterProfile, Event } from "@/types";
import { handleDownloadJson, handleDownloadICS } from "@/lib/exportUtils";
import { CourseCard } from "./CourseCard";

interface DashboardViewProps {
  semesterData: SemesterProfile;
  hasOriginalPdfs: boolean;
  reanalyzeStatus: { idx: number; message: string } | null;
  onReset: () => void;
  onUpdateEvent: (courseIdx: number, eventIdx: number, updatedEvent: Partial<Event>) => void;
  onAddEvent: (courseIdx: number, newEvent: Event) => void;
  onDeleteEvent: (courseIdx: number, eventIdx: number) => void;
  onReanalyzeCourse: (courseIdx: number) => void;
}

export function DashboardView({ semesterData, hasOriginalPdfs, reanalyzeStatus, onReset, onUpdateEvent, onAddEvent, onDeleteEvent, onReanalyzeCourse }: DashboardViewProps) {
  return (
    <div className="flex flex-col gap-8 max-w-6xl mx-auto w-full pb-20 pt-8 px-4">
      {/* The Global Header: Export and Settings */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 border-b border-border/50 pb-6">
        <div>
          <h1 className="text-4xl font-black tracking-tight text-primary">Semester Dashboard</h1>
          <p className="text-muted-foreground mt-2 text-lg">Your stateless aggregation and productivity router.</p>
        </div>
        <div className="flex flex-col sm:flex-row gap-3">
          <Button variant="outline" className="border-primary/20" onClick={onReset}>
            <UploadCloud className="w-4 h-4 mr-2" /> Upload More PDFs
          </Button>
          <Button variant="outline" onClick={() => handleDownloadJson(semesterData)} className="bg-muted/30">
            <FileJson className="w-4 h-4 mr-2" /> Save JSON
          </Button>
        </div>
      </div>

      {/* Global Calendar Export Area (2-Click Solution) */}
      <Card className="bg-primary/5 border-primary/20 shadow-lg">
        <CardContent className="p-6 md:p-8 flex flex-col lg:flex-row items-center gap-8">
          <div className="flex-1 space-y-4">
            <div>
              <Badge variant="secondary" className="mb-2 bg-primary/20 text-primary hover:bg-primary/30">Frictionless Export</Badge>
              <h2 className="text-2xl font-bold">Sync All Exams to Calendar</h2>
              <p className="text-muted-foreground mt-1">Export all exams from all courses into your preferred calendar app in exactly two clicks.</p>
            </div>
            <div className="flex flex-col sm:flex-row gap-4 pt-2">
              <Button size="lg" className="w-full sm:w-auto shadow-md shadow-primary/20" onClick={() => handleDownloadICS(semesterData)}>
                <Download className="w-5 h-5 mr-2" /> 1. Download Master .ICS
              </Button>
              <a href="https://calendar.google.com/calendar/r/settings/export" target="_blank" rel="noopener noreferrer" className={buttonVariants({ size: "lg", variant: "secondary", className: "w-full sm:w-auto border border-border/50" })}>
                <Calendar className="w-5 h-5 mr-2" /> 2. Import to Google Calendar <ExternalLink className="w-3 h-3 ml-2 opacity-50"/>
              </a>
            </div>
          </div>
          
          {/* Carousel for Instructions */}
          <div className="w-full lg:w-80 shrink-0">
            <Carousel className="w-full max-w-xs mx-auto">
              <CarouselContent>
                <CarouselItem>
                  <div className="p-1">
                    <Card className="border-0 shadow-none bg-background/50">
                      <CardContent className="flex flex-col items-center justify-center p-6 text-center space-y-3 min-h-[180px]">
                        <Download className="w-10 h-10 text-primary/50" />
                        <h3 className="font-semibold text-lg">Step 1: Download</h3>
                        <p className="text-sm text-muted-foreground">Click the download button to save the Combined_Exam_Schedule.ics file locally.</p>
                      </CardContent>
                    </Card>
                  </div>
                </CarouselItem>
                <CarouselItem>
                  <div className="p-1">
                    <Card className="border-0 shadow-none bg-background/50">
                      <CardContent className="flex flex-col items-center justify-center p-6 text-center space-y-3 min-h-[180px]">
                        <ExternalLink className="w-10 h-10 text-primary/50" />
                        <h3 className="font-semibold text-lg">Step 2: Open Google</h3>
                        <p className="text-sm text-muted-foreground">Click the second button to jump straight to the Google Calendar Import settings page.</p>
                      </CardContent>
                    </Card>
                  </div>
                </CarouselItem>
                <CarouselItem>
                  <div className="p-1">
                    <Card className="border-0 shadow-none bg-background/50">
                      <CardContent className="flex flex-col items-center justify-center p-6 text-center space-y-3 min-h-[180px]">
                        <Calendar className="w-10 h-10 text-primary/50" />
                        <h3 className="font-semibold text-lg">Step 3: Upload</h3>
                        <p className="text-sm text-muted-foreground">Under "Import", select the downloaded file, choose your calendar, and click Import!</p>
                      </CardContent>
                    </Card>
                  </div>
                </CarouselItem>
              </CarouselContent>
              <div className="flex justify-center gap-2 mt-2">
                <CarouselPrevious className="static transform-none h-8 w-8" />
                <CarouselNext className="static transform-none h-8 w-8" />
              </div>
            </Carousel>
          </div>
        </CardContent>
      </Card>

      {/* Aggregated Courses Grid */}
      <div className="space-y-8">
        <h2 className="text-2xl font-bold flex items-center">
          <BookOpen className="w-6 h-6 mr-3 text-primary" /> Course Aggregation
        </h2>
        
        <div className="grid grid-cols-1 gap-8">
          {semesterData.courses.map((course: any, idx: number) => (
            <CourseCard 
              key={idx} 
              course={course} 
              courseIdx={idx}
              hasOriginalPdfs={hasOriginalPdfs}
              reanalyzeStatus={reanalyzeStatus?.idx === idx ? reanalyzeStatus : null}
              onUpdateEvent={onUpdateEvent}
              onAddEvent={onAddEvent}
              onDeleteEvent={onDeleteEvent}
              onReanalyzeCourse={onReanalyzeCourse}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
