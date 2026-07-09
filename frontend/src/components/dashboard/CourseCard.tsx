"use client"
import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Button, buttonVariants } from "@/components/ui/button";
import { Download, Calendar, Copy, Search, BookOpen, Bot, MessageSquare, ExternalLink, X, BookMarked, Library } from "lucide-react";
import { CourseData } from "@/types";
import { handleExportCSV, generateAIPrompt, handleCopyPrompt } from "@/lib/exportUtils";

// Helper: Build a Google Calendar "Add Event" URL for a single exam (no OAuth needed)
function buildGoogleCalendarUrl(exam: any, courseTitle: string): string | null {
  if (!exam.Start_DateTime || exam.Start_DateTime.includes("Time not found")) return null;

  // Convert ISO datetime to Google Calendar format: YYYYMMDDTHHMMSS
  const formatDT = (dt: string) => dt.replace(/[-:]/g, "").replace(/\.\d{3}/, "");

  const start = formatDT(exam.Start_DateTime);
  const end = exam.End_DateTime ? formatDT(exam.End_DateTime) : start;

  const params = new URLSearchParams({
    action: "TEMPLATE",
    text: `${courseTitle} - ${exam.Event_Name}`,
    dates: `${start}/${end}`,
    details: `Format: ${exam.Format || "TBA"}\nWeightage: ${exam.Weightage || "N/A"}\nCourse: ${courseTitle}`,
  });

  return `https://calendar.google.com/calendar/u/0/r/eventedit?${params.toString()}`;
}

interface CourseCardProps {
  course: CourseData;
}

const DEFAULT_ACCORDION_STATE = ["exam-0"];

export function CourseCard({ course }: CourseCardProps) {
  const [zoomedImage, setZoomedImage] = useState<string | null>(null);

  return (
    <>
      <Card className="shadow-sm overflow-hidden border-border/50">
        <CardHeader className="bg-muted/20 border-b pb-4">
          <CardTitle className="text-2xl">{course.course_title}</CardTitle>
        </CardHeader>

        <CardContent className="p-0">
          <Tabs defaultValue="schedule" className="w-full">
            <div className="px-6 pt-4">
              <TabsList className="grid w-full grid-cols-2 h-11 bg-muted/30">
                <TabsTrigger value="schedule" className="text-sm md:text-base">Exams</TabsTrigger>
                {/* DISABLED: Syllabus tab commented out — uncomment when syllabus feature is ready */}
                {/* <TabsTrigger value="syllabus" className="text-sm md:text-base">Syllabus (AI)</TabsTrigger> */}
                <TabsTrigger value="books" className="text-sm md:text-base">Resources</TabsTrigger>
              </TabsList>
            </div>

            {/* ═══════════ EXAMS TAB — Accordion with per-exam Calendar buttons ═══════════ */}
            <TabsContent value="schedule" className="p-6">
              {course.evaluation_scheme.length > 0 ? (
                <Accordion defaultValue={DEFAULT_ACCORDION_STATE} className="w-full space-y-2">
                  {course.evaluation_scheme.map((exam: any, eIdx: number) => {
                    let dateDay = "";
                    let startTime = "";
                    let endTime = "";
                    let fallbackDate = exam.Start_DateTime || "Date TBA";

                    try {
                      if (exam.Start_DateTime && !exam.Start_DateTime.includes("Time not found")) {
                        const dateObj = new Date(exam.Start_DateTime);
                        dateDay = new Intl.DateTimeFormat('en-US', { weekday: 'short', month: 'short', day: 'numeric' }).format(dateObj);
                        startTime = new Intl.DateTimeFormat('en-US', { hour: 'numeric', minute: '2-digit' }).format(dateObj);

                        if (exam.End_DateTime) {
                          const endObj = new Date(exam.End_DateTime);
                          endTime = new Intl.DateTimeFormat('en-US', { hour: 'numeric', minute: '2-digit' }).format(endObj);
                        }
                      }
                    } catch (e) { /* graceful fallback */ }

                    const calUrl = buildGoogleCalendarUrl(exam, course.course_title);

                    return (
                      <AccordionItem key={eIdx} value={`exam-${eIdx}`} className="border rounded-lg px-4 bg-background">
                        <AccordionTrigger className="hover:no-underline py-3 text-left">
                          <div className="flex flex-1 items-center justify-between mr-4 gap-4">
                            <span className="font-semibold">{exam.Event_Name}</span>
                            <span className="text-muted-foreground text-sm shrink-0">{dateDay || fallbackDate}</span>
                          </div>
                        </AccordionTrigger>
                        <AccordionContent className="pb-4">
                          <div className="space-y-3 pt-2 border-t border-border/30">
                            {/* Date & Time */}
                            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm pt-2">
                              <span className="flex items-center gap-1.5">
                                📅 <strong>{dateDay || "Date TBA"}</strong>
                              </span>
                              {startTime && (
                                <span className="flex items-center gap-1.5">
                                  ⏰ {startTime}{endTime ? ` → ${endTime}` : ""}
                                </span>
                              )}
                            </div>

                            {/* Format & Weightage */}
                            <div className="flex flex-wrap gap-2">
                              {exam.Format && <Badge variant="outline">{exam.Format}</Badge>}
                              {exam.Weightage && <Badge variant="secondary">{exam.Weightage}</Badge>}
                            </div>

                            {/* Add to Google Calendar */}
                            {calUrl && (
                              <a
                                href={calUrl}
                                target="_blank"
                                rel="noopener noreferrer"
                                className={buttonVariants({ variant: "outline", size: "sm", className: "w-full sm:w-auto mt-1" })}
                              >
                                <Calendar className="w-4 h-4 mr-2" /> Add to Google Calendar
                              </a>
                            )}
                          </div>
                        </AccordionContent>
                      </AccordionItem>
                    );
                  })}
                </Accordion>
              ) : (
                <p className="text-muted-foreground italic">No exams found for this course.</p>
              )}
            </TabsContent>

            {/* ═══════════ SYLLABUS TAB — DISABLED ═══════════ */}
            {/* Uncomment the TabsTrigger above AND this entire block to re-enable syllabus.
                Also re-enable SYLLABUS in the backend router prompt + orchestrator fan-out.

            <TabsContent value="syllabus" className="p-6">
              {course.syllabus_topics.length > 0 ? (
                <div className="space-y-4">
                  <div className="flex justify-end">
                    <Button variant="outline" size="sm" onClick={() => handleExportCSV(course.course_title, course.syllabus_topics)}>
                      <Download className="w-4 h-4 mr-2" /> Export to Notion (CSV)
                    </Button>
                  </div>
                  <Accordion className="w-full bg-background rounded-lg border">
                    {course.syllabus_topics.map((topic: any, tIdx: number) => (
                      <AccordionItem key={tIdx} value={`topic-${tIdx}`} className="border-b last:border-0 px-4">
                        <AccordionTrigger className="hover:no-underline py-4 text-left">
                          <div className="flex flex-1 items-center justify-between mr-4 gap-4">
                            <span className="font-medium text-base">{topic.module_name}</span>
                            <Badge variant="outline" className="shrink-0">{topic.number_of_lectures} Lec</Badge>
                          </div>
                        </AccordionTrigger>
                        <AccordionContent className="pb-4 pt-1">
                          <div className="flex flex-wrap gap-2 pt-2 border-t border-border/30 mt-2">
                            <a href={`https://chatgpt.com/?q=${generateAIPrompt(course.course_title, [topic])}`} target="_blank" rel="noopener noreferrer" className={buttonVariants({ variant: "outline", size: "sm" })}>
                              <Bot className="w-4 h-4 mr-2" /> Ask ChatGPT
                            </a>
                            <a href={`https://www.perplexity.ai/search?q=${generateAIPrompt(course.course_title, [topic])}`} target="_blank" rel="noopener noreferrer" className={buttonVariants({ variant: "outline", size: "sm" })}>
                              <Search className="w-4 h-4 mr-2" /> Perplexity
                            </a>
                            <a href={`https://copilot.microsoft.com/?q=${generateAIPrompt(course.course_title, [topic])}`} target="_blank" rel="noopener noreferrer" className={buttonVariants({ variant: "outline", size: "sm" })}>
                              <MessageSquare className="w-4 h-4 mr-2" /> Copilot
                            </a>
                            <Separator orientation="vertical" className="h-9 mx-1 hidden sm:block" />
                            <Button size="sm" variant="secondary" onClick={() => handleCopyPrompt(course.course_title, [topic])}>
                              <Copy className="w-4 h-4 mr-2" /> Copy Prompt <span className="hidden sm:inline">&nbsp;(Claude/Gemini)</span>
                            </Button>
                          </div>
                        </AccordionContent>
                      </AccordionItem>
                    ))}
                  </Accordion>
                </div>
              ) : (
                <p className="text-muted-foreground italic">No syllabus found for this course.</p>
              )}
            </TabsContent>

            */}

            {/* ═══════════ RESOURCES TAB ═══════════ */}
            <TabsContent value="books" className="p-6">
              {course.references.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {course.references.map((book: any, bIdx: number) => (
                    <Card key={bIdx} className="bg-background shadow-none border-border/60 hover:border-primary/30 transition-colors">
                      <CardContent className="p-4 flex flex-col h-full">
                        <div className="flex items-start gap-4 mb-4">
                          {book.thumbnail_url ? (
                            <img
                              src={book.thumbnail_url}
                              alt="Cover"
                              className="w-16 h-24 object-cover rounded shadow-sm shrink-0 cursor-pointer hover:opacity-80 hover:scale-105 transition-all"
                              title="Click to enlarge"
                              onClick={() => setZoomedImage(book.thumbnail_url)}
                            />
                          ) : (
                            <div className="w-16 h-24 bg-muted rounded flex items-center justify-center shrink-0">
                              <BookOpen className="w-6 h-6 text-muted-foreground/50" />
                            </div>
                          )}
                          <div>
                            <h4 className="font-semibold text-base leading-snug line-clamp-2">{book.title}</h4>
                            <p className="text-muted-foreground text-sm mt-1">{book.author || "Unknown Author"}</p>
                          </div>
                        </div>

                        <div className="flex flex-col gap-2 mt-auto pt-3 border-t border-border/30">
                          {/* Buy → Google Shopping with title + author for better results */}
                          <a
                            href={`https://www.google.com/search?tbm=shop&q=${encodeURIComponent(`${book.title} ${book.author || ""}`.trim())}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className={buttonVariants({ variant: "default", size: "sm", className: "w-full" })}
                          >
                            <Search className="w-4 h-4 mr-2" /> Buy (Google Shopping)
                          </a>
                          {/* Free PDF — Multiple source options */}
                          <div className="grid grid-cols-2 gap-2">
                            <a
                              href={`https://annas-archive.gl/search?q=${encodeURIComponent(`${book.title} ${book.author || ""}`.trim())}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className={buttonVariants({ variant: "secondary", size: "sm", className: "w-full text-xs" })}
                            >
                              <BookMarked className="w-3.5 h-3.5 mr-1.5" /> Anna&#39;s Archive
                            </a>
                            <a
                              href={`https://libgen.li/index.php?req=${encodeURIComponent(`${book.title} ${book.author || ""}`.trim())}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className={buttonVariants({ variant: "secondary", size: "sm", className: "w-full text-xs" })}
                            >
                              <Library className="w-3.5 h-3.5 mr-1.5" /> LibGen
                            </a>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              ) : (
                <p className="text-muted-foreground italic">No textbooks found for this course.</p>
              )}
            </TabsContent>

          </Tabs>
        </CardContent>
      </Card>

      {/* ═══════════ Image Zoom Modal ═══════════ */}
      {zoomedImage && (
        <div
          className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-8 cursor-pointer backdrop-blur-sm"
          onClick={() => setZoomedImage(null)}
        >
          <button
            className="absolute top-6 right-6 text-white/80 hover:text-white transition-colors"
            onClick={() => setZoomedImage(null)}
            aria-label="Close zoom"
          >
            <X className="w-8 h-8" />
          </button>
          <img
            src={zoomedImage}
            alt="Book cover enlarged"
            className="max-h-[80vh] max-w-[90vw] object-contain rounded-lg shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          />
        </div>
      )}
    </>
  );
}
