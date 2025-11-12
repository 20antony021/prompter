"use client";

import { Button } from "@/components/ui/button";
import { Plus, WandSparkles, Check, Loader } from "lucide-react";
import { useFormStatus } from "react-dom";

const Icon = {
  plus: Plus,
  "wand-sparkles": WandSparkles,
  check: Check,
};

export function SubmitButton({
  loadingText,
  buttonText,
  icon,
}: {
  loadingText: string;
  buttonText: string;
  icon: keyof typeof Icon;
}) {
  const { pending } = useFormStatus();

  const IconComponent = Icon[icon];

  return (
    <Button
      type="submit"
      disabled={pending}
      className="gap-2 w-full sm:w-auto bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm"
    >
      {pending ? (
        <Loader className="h-4 w-4 animate-spin" />
      ) : (
        <IconComponent className="h-4 w-4" />
      )}
      {pending ? loadingText : buttonText}
    </Button>
  );
}
