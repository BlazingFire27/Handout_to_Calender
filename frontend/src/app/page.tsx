"use client"
import { useState, useCallback, useRef } from "react";
import { toast } from "sonner";
import { SemesterProfile, CourseData, Event } from "@/types";

import { UploadOptions } from "@/components/upload/UploadOptions";
import { UploadJson } from "@/components/upload/UploadJson";
import { UploadPdf } from "@/components/upload/UploadPdf";
import { DashboardView } from "@/components/dashboard/DashboardView";

export default function Home() {
  const [view, setView] = useState<"options" | "upload-json" | "upload-pdf" | "dashboard">("options");
  const [semesterData, setSemesterData] = useState<SemesterProfile | null>(null);

  // PDF State
  const [pdfFiles, setPdfFiles] = useState<File[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [processStatus, setProcessStatus] = useState("");
  const [fileStatuses, setFileStatuses] = useState<Record<string, string>>({});

  // JSON Dropzone Logic
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

  // PDF Dropzone Logic
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
    
    let totalEvents = 0;
    let totalSyllabus = 0;
    let totalRefs = 0;
    
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

        let watchdogTimer: NodeJS.Timeout | undefined;
        const resetWatchdog = () => {
          clearTimeout(watchdogTimer);
          watchdogTimer = setTimeout(() => {
            console.error(`Watchdog timeout for ${file.name} - No data for 13 minutes`);
            abortControllerRef.current?.abort();
          }, 780000); // 13 minutes
        };

        resetWatchdog();

        while (true) {
          const { done, value } = await reader.read();
          resetWatchdog();

          if (done) {
            clearTimeout(watchdogTimer);
            break;
          }

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
                totalRefs += data.refs_found || 0;
                
                setProcessStatus(`Extracted ${totalEvents} exams and ${totalRefs} textbooks so far...`);
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
          setFileStatuses(prev => ({ ...prev, [file.name]: "🛑 Cancelled / Timeout" }));
        } else {
          setFileStatuses(prev => ({ ...prev, [file.name]: "❌ Error" }));
        }
      } finally {
        // We can't clear the timeout easily here without making it accessible,
        // but the timeout triggers an abort anyway which cleans it up.
      }
    };

    // Parallelize all PDF requests
    await Promise.all(pdfFiles.map((file, i) => processFile(file, i)));

    if (!abortControllerRef.current?.signal.aborted) {
      if (aggregatedCourses.length === 0) {
        toast.error("No data extracted", {
          description: "No schedules, syllabus, or textbooks were found in the uploaded PDFs."
        });
        setIsProcessing(false);
        setProcessStatus("");
        setProgress(0);
      } else {
        setProcessStatus("Finalizing dashboard...");
        setSemesterData({ courses: aggregatedCourses });
        setIsProcessing(false);
        setView("dashboard");
        toast.success("Extraction Complete!", {
          description: "Save this JSON for instant access next time.",
        });
      }
    }
  };

  const handleUpdateEvent = useCallback((courseIdx: number, eventIdx: number, updatedEvent: Partial<Event>) => {
    setSemesterData((prev) => {
      if (!prev) return null;
      const updatedCourses = prev.courses.map((course, cIdx) => {
        if (cIdx !== courseIdx) return course;
        const updatedScheme = course.evaluation_scheme.map((event, eIdx) => {
          if (eIdx !== eventIdx) return event;
          return { ...event, ...updatedEvent };
        });
        return { ...course, evaluation_scheme: updatedScheme };
      });
      return { ...prev, courses: updatedCourses };
    });
    toast.success("JSON Profile Updated!", {
      description: "Please download the updated JSON file to preserve your changes.",
    });
  }, []);

  if (view === "options") {
    return <UploadOptions onSelect={setView} />;
  }

  if (view === "upload-json") {
    return <UploadJson onBack={() => setView("options")} onDrop={onDropJson} />;
  }

  if (view === "upload-pdf") {
    return (
      <UploadPdf 
        onBack={() => { setView("options"); setPdfFiles([]); }} 
        onDrop={onDropPdf} 
        pdfFiles={pdfFiles}
        onRemovePdf={removePdf}
        onClearPdfs={() => setPdfFiles([])}
        isProcessing={isProcessing}
        progress={progress}
        processStatus={processStatus}
        fileStatuses={fileStatuses}
        onExtract={handlePdfProcessing}
        onCancel={() => {
          abortControllerRef.current?.abort();
          setIsProcessing(false);
          setProcessStatus("");
          setProgress(0);
        }}
      />
    );
  }



  if (view === "dashboard" && semesterData) {
    return (
      <DashboardView 
        semesterData={semesterData} 
        onReset={() => {
          setView("options");
          setPdfFiles([]);
          setSemesterData(null);
        }}
        onUpdateEvent={handleUpdateEvent}
      />
    );
  }

  return null;
}
