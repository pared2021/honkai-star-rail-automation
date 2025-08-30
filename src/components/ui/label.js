import { jsx as _jsx } from "react/jsx-runtime";
import React from 'react';
import { cn } from '../../utils/cn';
import { cva } from 'class-variance-authority';
const labelVariants = cva("text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70");
const Label = React.forwardRef(({ className, ...props }, ref) => (_jsx("label", { ref: ref, className: cn(labelVariants(), className), ...props })));
Label.displayName = "Label";
export { Label };
