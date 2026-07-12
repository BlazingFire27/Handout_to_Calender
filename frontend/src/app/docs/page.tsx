"use client"

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowLeft, Upload, Download, Pencil, Calendar, Shield, AlertTriangle, X } from "lucide-react";
import Link from "next/link";

export default function DocsPage() {
  const [zoomedImage, setZoomedImage] = useState<string | null>(null);

  return (
    <div className="flex flex-col gap-10 max-w-4xl mx-auto w-full pb-16">
      {/* Back button */}
      <div>
        <Link href="/" className="inline-flex items-center gap-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors font-medium">
          <ArrowLeft className="w-4 h-4" /> Back to Home
        </Link>
      </div>

      {/* Header */}
      <div className="flex flex-col gap-2">
        <h1 className="text-4xl font-extrabold tracking-tight bg-gradient-to-r from-primary to-primary-foreground bg-clip-text text-transparent">
          User Guide
        </h1>
        <p className="text-lg text-muted-foreground">
          Learn how to parse handouts, modify schedules, and import them into your calendar.
        </p>
      </div>

      {/* Step by Step Guide */}
      <div className="space-y-8">
        <h2 className="text-2xl font-bold tracking-tight border-b pb-2 flex items-center gap-2">
          <Calendar className="w-6 h-6 text-primary" /> Step by Step Walkthrough
        </h2>

        <div className="flex flex-col gap-8">
          {/* Step 1: Upload */}
          <Card className="overflow-hidden border-border/60 hover:border-border transition-colors">
            <CardHeader className="space-y-1 pb-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-primary">Step 1</span>
                <Upload className="w-5 h-5 text-muted-foreground" />
              </div>
              <CardTitle className="text-2xl">Upload Handouts</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground leading-relaxed">
                Drag and drop your syllabus or evaluation handouts into the PDF section. You can upload up to 20 files at a time.
              </p>
              <div className="w-full flex justify-center bg-muted/5 rounded-lg border border-border/40 p-2 md:p-4">
                <img
                  src="/images/docs/upload_pdf.png"
                  alt="Upload handouts screen"
                  className="rounded-md border border-border/30 cursor-zoom-in hover:brightness-95 transition-all w-full max-w-3xl h-auto object-contain max-h-[500px] shadow-sm"
                  onClick={() => setZoomedImage("/images/docs/upload_pdf.png")}
                />
              </div>
            </CardContent>
          </Card>

          {/* Step 2: Export JSON */}
          <Card className="overflow-hidden border-border/60 hover:border-border transition-colors">
            <CardHeader className="space-y-1 pb-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-primary">Step 2</span>
                <Download className="w-5 h-5 text-muted-foreground" />
              </div>
              <CardTitle className="text-2xl">Backup Your Data</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground leading-relaxed">
                Click Save JSON to download your profile. Since the app is stateless, keeping this file allows you to restore your dashboard instantly later.
              </p>
              <div className="w-full flex justify-center bg-muted/5 rounded-lg border border-border/40 p-2 md:p-4">
                <img
                  src="/images/docs/export.png"
                  alt="Save JSON screen"
                  className="rounded-md border border-border/30 cursor-zoom-in hover:brightness-95 transition-all w-full max-w-3xl h-auto object-contain max-h-[500px] shadow-sm"
                  onClick={() => setZoomedImage("/images/docs/export.png")}
                />
              </div>
            </CardContent>
          </Card>

          {/* Step 3: Edit Event */}
          <Card className="overflow-hidden border-border/60 hover:border-border transition-colors">
            <CardHeader className="space-y-1 pb-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-primary">Step 3</span>
                <Pencil className="w-5 h-5 text-muted-foreground" />
              </div>
              <CardTitle className="text-2xl">Correct and Refine</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground leading-relaxed">
                Examine your schedule on the dashboard. Click Edit Event on any card to update names, format, weightage, dates, or specific times.
              </p>
              <div className="w-full flex justify-center bg-muted/5 rounded-lg border border-border/40 p-2 md:p-4">
                <img
                  src="/images/docs/edit_event.png"
                  alt="Edit event modal"
                  className="rounded-md border border-border/30 cursor-zoom-in hover:brightness-95 transition-all w-full max-w-3xl h-auto object-contain max-h-[500px] shadow-sm"
                  onClick={() => setZoomedImage("/images/docs/edit_event.png")}
                />
              </div>
            </CardContent>
          </Card>

          {/* Step 4: Import Calendar */}
          <Card className="overflow-hidden border-border/60 hover:border-border transition-colors">
            <CardHeader className="space-y-1 pb-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-primary">Step 4</span>
                <Calendar className="w-5 h-5 text-muted-foreground" />
              </div>
              <CardTitle className="text-2xl">Sync to Your Calendar</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground leading-relaxed">
                Export the master ICS file. Open Google Calendar, head to Settings, and select Import to upload the ICS file and sync your schedules.
              </p>
              <div className="w-full flex justify-center bg-muted/5 rounded-lg border border-border/40 p-2 md:p-4">
                <img
                  src="/images/docs/import_button.png"
                  alt="Google Calendar import settings"
                  className="rounded-md border border-border/30 cursor-zoom-in hover:brightness-95 transition-all w-full max-w-3xl h-auto object-contain max-h-[500px] shadow-sm"
                  onClick={() => setZoomedImage("/images/docs/import_button.png")}
                />
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Guidelines & Limits */}
      <div className="space-y-6 pt-6">
        <h2 className="text-2xl font-bold tracking-tight border-b pb-2 flex items-center gap-2">
          <Shield className="w-6 h-6 text-primary" /> Rules and Guidelines
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card className="bg-muted/10 border-border/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-base flex items-center gap-2 font-semibold">
                <AlertTriangle className="w-4 h-4 text-amber-500" /> Processing Limits
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground space-y-2 leading-relaxed">
              <p>
                To keep server requests reliable and prevent timeout failures, the app limits document processing to 20 files per session.
              </p>
              <p>
                If you have more than 20 handouts, combine related files or load them in separate sessions.
              </p>
            </CardContent>
          </Card>

          <Card className="bg-muted/10 border-border/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-base flex items-center gap-2 font-semibold">
                <Shield className="w-4 h-4 text-emerald-500" /> Privacy Policy
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground space-y-2 leading-relaxed">
              <p>
                We do not track or save your uploads. The backend parses files in real time and streams the results straight back to you.
              </p>
              <p>
                Once you close the browser tab, all session data is removed. Save your JSON file to keep your progress.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Image Zoom Modal */}
      {zoomedImage && (
        <div
          className="fixed inset-0 z-50 bg-black/85 flex items-center justify-center p-4 md:p-8 cursor-zoom-out backdrop-blur-sm"
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
            alt="Enlarged screenshot"
            className="max-w-[95vw] max-h-[90vh] object-contain rounded-lg shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          />
        </div>
      )}
    </div>
  );
}
