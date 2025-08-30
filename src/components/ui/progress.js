import { jsx as _jsx } from "react/jsx-runtime";
import React from 'react';
import { cn } from '../../utils/cn';
const Progress = React.forwardRef(({ className, value = 0, max = 100, ...props }, ref) => {
    const percentage = Math.min(Math.max((value / max) * 100, 0), 100);
    return (_jsx("div", { ref: ref, className: cn("relative h-4 w-full overflow-hidden rounded-full bg-secondary", className), ...props, children: _jsx("div", { className: "h-full w-full flex-1 bg-primary transition-all", style: {
                transform: `translateX(-${100 - percentage}%)`
            } }) }));
});
Progress.displayName = "Progress";
export { Progress };
