"use client";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { createTopicFromUrl, CreateTopicState } from "./actions";
import { SubmitButton } from "@/components/submit-button";
import { useEffect, useState } from "react";
import { useFormState } from "react-dom";
import { AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface CreateTopicDialogProps {
  children: React.ReactNode;
}

const initialState: CreateTopicState = {};

export function CreateTopicDialog({ children }: CreateTopicDialogProps) {
  const [state, formAction] = useFormState(createTopicFromUrl, initialState);
  const [open, setOpen] = useState(false);
  const [formKey, setFormKey] = useState(0);

  // Close dialog on each successful creation (track id so it closes every time)
  useEffect(() => {
    if (state?.topicId) {
      setOpen(false);
    }
  }, [state?.topicId]);

  return (
    <Dialog
      open={open}
      onOpenChange={(v) => {
        setOpen(v);
        if (v) setFormKey((k) => k + 1); // remount form to reset useFormState
      }}
    >
      <DialogTrigger asChild>{children}</DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <form action={formAction} key={formKey}>
          <DialogHeader>
            <DialogTitle>Add New Topic</DialogTitle>
            <DialogDescription>
              Enter a website URL to automatically create a topic with extracted
              information.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <label htmlFor="url" className="text-sm font-medium">
                Website URL
              </label>
              <Input
                id="url"
                name="url"
                type="url"
                placeholder="https://google.com"
                required
                autoFocus
              />
            </div>
            {state?.error && (
              <div
                className={cn(
                  "flex items-start gap-3 p-4 border rounded-lg",
                  "bg-destructive/5 border-destructive/20 text-destructive"
                )}
              >
                <AlertCircle className="h-5 w-5 mt-0.5 shrink-0" />
                <div className="space-y-1">
                  <p className="text-sm font-medium">Error</p>
                  <p className="text-sm opacity-80">{state.error}</p>
                </div>
              </div>
            )}
          </div>
          <DialogFooter>
            <SubmitButton
              loadingText="Creating..."
              buttonText="Create Topic"
              icon="plus"
            />
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
