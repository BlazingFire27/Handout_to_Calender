"use client"
import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Button, buttonVariants } from "@/components/ui/button";
import { Download, Calendar, Copy, Search, BookOpen, Bot, MessageSquare, ExternalLink, X, BookMarked, Library, Pencil, RefreshCw, Loader2, Trash2, Plus } from "lucide-react";
import { CourseData, Event } from "@/types";
import { handleExportCSV, generateAIPrompt, handleCopyPrompt } from "@/lib/exportUtils";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";

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
  courseIdx: number;
  hasOriginalPdfs: boolean;
  reanalyzeStatus?: { idx: number; message: string } | null;
  onUpdateEvent: (courseIdx: number, eventIdx: number, updatedEvent: Partial<Event>) => void;
  onAddEvent: (courseIdx: number, newEvent: Event) => void;
  onDeleteEvent: (courseIdx: number, eventIdx: number) => void;
  onReanalyzeCourse: (courseIdx: number) => void;
}

const DEFAULT_ACCORDION_STATE = ["exam-0"];

export function CourseCard({ course, courseIdx, hasOriginalPdfs, reanalyzeStatus, onUpdateEvent, onAddEvent, onDeleteEvent, onReanalyzeCourse }: CourseCardProps) {
  const [zoomedImage, setZoomedImage] = useState<string | null>(null);

  // Editing state
  const [editingEvent, setEditingEvent] = useState<{ courseIdx: number; eventIdx: number; exam: Event } | null>(null);

  // Form states
  const [eventName, setEventName] = useState("");
  const [eventDate, setEventDate] = useState("");
  const [isAllDay, setIsAllDay] = useState(false);
  const [startTime, setStartTime] = useState("");
  const [endTime, setEndTime] = useState("");
  const [eventFormat, setEventFormat] = useState("");
  const [eventWeightage, setEventWeightage] = useState("");

  useEffect(() => {
    if (editingEvent) {
      const exam = editingEvent.exam;
      setEventName(exam.Event_Name || "");
      setEventFormat(exam.Format || "");
      setEventWeightage(exam.Weightage || "");

      let dateStr = "";
      let startStr = "";
      let endStr = "";

      if (exam.Start_DateTime) {
        const parts = exam.Start_DateTime.split("T");
        dateStr = parts[0];
        if (parts[1]) {
          startStr = parts[1].substring(0, 5); // "HH:MM"
        }
      }
      if (exam.End_DateTime) {
        const parts = exam.End_DateTime.split("T");
        if (parts[1]) {
          endStr = parts[1].substring(0, 5); // "HH:MM"
        }
      }

      setEventDate(dateStr);

      const allDay = startStr === "00:00" && (endStr === "23:59" || endStr === "23:59:59");
      setIsAllDay(allDay);
      setStartTime(allDay ? "" : startStr);
      setEndTime(allDay ? "" : endStr);
    }
  }, [editingEvent]);

  const handleSave = () => {
    if (!editingEvent) return;

    let finalStart = "";
    let finalEnd = "";

    if (isAllDay) {
      finalStart = `${eventDate}T00:00:00`;
      finalEnd = `${eventDate}T23:59:59`;
    } else {
      const start = startTime || "00:00";
      const end = endTime || "23:59";
      finalStart = `${eventDate}T${start}:00`;
      finalEnd = `${eventDate}T${end}:00`;
    }

    const subjectPrefix = isAllDay ? "⚠️ TIME TBA: " : "";
    const subject = `${subjectPrefix}${course.course_title.toUpperCase()} + ${eventName}`;

    const updated: Partial<Event> = {
      Event_Name: eventName,
      Start_DateTime: finalStart,
      End_DateTime: finalEnd,
      Format: eventFormat,
      Weightage: eventWeightage,
      Subject: subject
    };

    if (editingEvent.eventIdx >= course.evaluation_scheme.length) {
      onAddEvent(courseIdx, updated as Event);
    } else {
      onUpdateEvent(editingEvent.courseIdx, editingEvent.eventIdx, updated);
    }
    
    setEditingEvent(null);
  };

  return (
    <>
      <Card className="shadow-sm overflow-hidden border-border/50">
        <CardHeader className="bg-muted/20 border-b pb-4 flex flex-row items-center justify-between">
          <CardTitle className="text-2xl m-0 flex items-center gap-4">
            {course.course_title}
            {reanalyzeStatus && (
              <span className="text-sm font-normal text-muted-foreground flex items-center bg-muted px-3 py-1 rounded-full animate-pulse">
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                {reanalyzeStatus.message}
              </span>
            )}
          </CardTitle>
          {hasOriginalPdfs && !reanalyzeStatus && (
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => onReanalyzeCourse(courseIdx)}
              className="text-primary hover:bg-primary hover:text-primary-foreground transition-colors"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Re-Analyze
            </Button>
          )}
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
                <Accordion multiple defaultValue={DEFAULT_ACCORDION_STATE} className="w-full space-y-2">
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

                        if (startTime === "12:00 AM" && (endTime === "11:59 PM" || !endTime)) {
                          startTime = "Not specified in handout";
                          endTime = "Not specified in handout";
                        }
                      }
                    } catch (e) { /* graceful fallback */ }

                    const calUrl = buildGoogleCalendarUrl(exam, course.course_title);

                    return (
                      <AccordionItem key={eIdx} value={`exam-${eIdx}`} className="border rounded-lg px-4 bg-background">
                        <AccordionTrigger className="hover:no-underline py-3 text-left group">
                          <div className="flex flex-1 items-center justify-between mr-4 gap-4">
                            <span className="font-semibold">{exam.Event_Name}</span>
                            <div className="flex items-center gap-4">
                              <span className="text-muted-foreground text-sm shrink-0">{dateDay || fallbackDate}</span>
                              <div
                                role="button"
                                tabIndex={0}
                                className="flex items-center justify-center w-6 h-6 rounded-md opacity-0 group-hover:opacity-100 transition-opacity text-destructive hover:bg-destructive/10 cursor-pointer"
                                onClick={(e) => {
                                  e.preventDefault();
                                  e.stopPropagation();
                                  onDeleteEvent(courseIdx, eIdx);
                                }}
                              >
                                <Trash2 className="w-4 h-4" />
                              </div>
                            </div>
                          </div>
                        </AccordionTrigger>
                        <AccordionContent className="pb-4">
                          <div className="space-y-3 pt-2 border-t border-border/30">
                            {/* Date, Time, Format & Weightage */}
                            <div className="flex flex-col gap-1 text-sm pt-2">
                              <span><strong>Date (Day):</strong> {dateDay ? dateDay : "Date TBA"}</span>
                              <span><strong>Start Time:</strong> {startTime ? startTime : "NA"}</span>
                              <span><strong>End Time:</strong> {endTime ? endTime : "NA"}</span>
                              <span><strong>Type:</strong> {exam.Format ? exam.Format : "NA"}</span>
                              <span><strong>Weightage:</strong> {exam.Weightage ? exam.Weightage : "NA"}</span>
                            </div>

                            {/* Actions: Add to Google Calendar & Edit Details */}
                            <div className="flex flex-col sm:flex-row gap-2 pt-1">
                              {calUrl && (
                                <a
                                  href={calUrl}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className={buttonVariants({ variant: "outline", size: "sm", className: "w-full sm:w-auto" })}
                                >
                                  <Calendar className="w-4 h-4 mr-2" /> Add to Google Calendar
                                </a>
                              )}
                              <Button
                                variant="outline"
                                size="sm"
                                className="w-full sm:w-auto"
                                onClick={() => setEditingEvent({ courseIdx, eventIdx: eIdx, exam })}
                              >
                                <Pencil className="w-4 h-4 mr-2" /> Edit Event
                              </Button>
                            </div>
                          </div>
                        </AccordionContent>
                      </AccordionItem>
                    );
                  })}
                </Accordion>
              ) : (
                <p className="text-muted-foreground italic mb-4">No exams found for this course.</p>
              )}
              
              <Button 
                variant="outline" 
                className="w-full mt-4 border-dashed border-2 hover:bg-muted/50 text-muted-foreground hover:text-foreground"
                onClick={() => {
                  const newBlankExam: Event = {
                    Event_Name: "",
                    Start_DateTime: "",
                    End_DateTime: "",
                    Format: "",
                    Weightage: "",
                    Subject: course.course_title
                  };
                  setEditingEvent({ courseIdx, eventIdx: course.evaluation_scheme.length, exam: newBlankExam });
                }}
              >
                <Plus className="w-4 h-4 mr-2" /> Add Exam Component
              </Button>
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
            src={zoomedImage.replace("zoom=1", "zoom=0").replace("&edge=curl", "")}
            alt="Book cover enlarged"
            className="w-[90vw] h-[90vh] object-contain rounded-lg shadow-2xl"
            onClick={(e) => e.stopPropagation()}
            onLoad={(e) => {
              const img = e.currentTarget;
              // Google Books API often returns a generic wide placeholder (text on white) if a high-res cover is missing.
              // Since real textbook covers are portrait, if width > height, it's definitely a placeholder.
              if (img.naturalWidth > img.naturalHeight && img.src !== zoomedImage) {
                img.src = zoomedImage; // Fallback to original thumbnail
              }
            }}
            onError={(e) => {
              if (e.currentTarget.src !== zoomedImage) {
                e.currentTarget.src = zoomedImage;
              }
            }}
          />
        </div>
      )}
      {/* ═══════════ Event Edit Modal ═══════════ */}
      {editingEvent && (
        <Dialog open={!!editingEvent} onOpenChange={(open) => { if (!open) setEditingEvent(null); }}>
          <DialogContent className="sm:max-w-md w-full bg-card text-card-foreground border border-border rounded-lg shadow-xl p-6">
            <DialogHeader className="mb-4">
              <DialogTitle className="text-xl font-bold flex items-center gap-2 text-primary">
                <Pencil className="w-5 h-5" /> Edit Event Details
              </DialogTitle>
              <p className="text-sm text-muted-foreground">Modify extracted details for this academic event.</p>
            </DialogHeader>

            <div className="space-y-4">
              {/* Event Name */}
              <div className="space-y-1">
                <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block">Event Name</label>
                <input
                  type="text"
                  value={eventName}
                  onChange={(e) => setEventName(e.target.value)}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  placeholder="e.g. Mid-Sem Exam"
                />
              </div>

              {/* Event Date */}
              <div className="space-y-1">
                <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block">Event Date</label>
                <input
                  type="date"
                  value={eventDate}
                  onChange={(e) => setEventDate(e.target.value)}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                />
              </div>

              {/* All Day Event Checkbox */}
              <div className="flex items-center gap-2 py-1">
                <input
                  type="checkbox"
                  id="all-day-checkbox"
                  checked={isAllDay}
                  onChange={(e) => setIsAllDay(e.target.checked)}
                  className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                />
                <label htmlFor="all-day-checkbox" className="text-sm font-medium text-foreground select-none cursor-pointer">
                  All Day / Time Not Specified
                </label>
              </div>

              {/* Start & End Times */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block">Start Time</label>
                  <input
                    type="time"
                    value={startTime}
                    disabled={isAllDay}
                    onChange={(e) => setStartTime(e.target.value)}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block">End Time</label>
                  <input
                    type="time"
                    value={endTime}
                    disabled={isAllDay}
                    onChange={(e) => setEndTime(e.target.value)}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  />
                </div>
              </div>

              {/* Format & Weightage */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block">Type / Format</label>
                  <input
                    type="text"
                    value={eventFormat}
                    onChange={(e) => setEventFormat(e.target.value)}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                    placeholder="e.g. CB or OB"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block">Weightage</label>
                  <input
                    type="text"
                    value={eventWeightage}
                    onChange={(e) => setEventWeightage(e.target.value)}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                    placeholder="e.g. 25%"
                  />
                </div>
              </div>
            </div>

            <DialogFooter className="mt-6 flex justify-end gap-3 border-t border-border/50 pt-4">
              <Button variant="outline" onClick={() => setEditingEvent(null)}>
                Cancel
              </Button>
              <Button onClick={handleSave} disabled={!eventName || !eventDate}>
                Save Changes
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
    </>
  );
}
