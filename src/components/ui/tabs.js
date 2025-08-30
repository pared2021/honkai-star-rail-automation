import { jsx as _jsx } from "react/jsx-runtime";
import React from 'react';
import { cn } from '../../utils/cn';
const TabsContext = React.createContext(undefined);
const useTabs = () => {
    const context = React.useContext(TabsContext);
    if (!context) {
        throw new Error('useTabs must be used within a Tabs component');
    }
    return context;
};
const Tabs = ({ value, defaultValue, onValueChange, children, className }) => {
    const [internalValue, setInternalValue] = React.useState(defaultValue || '');
    const currentValue = value !== undefined ? value : internalValue;
    const handleValueChange = onValueChange || setInternalValue;
    return (_jsx(TabsContext.Provider, { value: { value: currentValue, onValueChange: handleValueChange }, children: _jsx("div", { className: cn('w-full', className), children: children }) }));
};
const TabsList = React.forwardRef(({ className, ...props }, ref) => (_jsx("div", { ref: ref, className: cn("inline-flex h-10 items-center justify-center rounded-md bg-muted p-1 text-muted-foreground", className), ...props })));
TabsList.displayName = "TabsList";
const TabsTrigger = React.forwardRef(({ className, value, ...props }, ref) => {
    const { value: selectedValue, onValueChange } = useTabs();
    const isSelected = selectedValue === value;
    return (_jsx("button", { ref: ref, className: cn("inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50", isSelected
            ? "bg-background text-foreground shadow-sm"
            : "text-muted-foreground hover:text-foreground", className), onClick: () => onValueChange(value), ...props }));
});
TabsTrigger.displayName = "TabsTrigger";
const TabsContent = React.forwardRef(({ className, value, ...props }, ref) => {
    const { value: selectedValue } = useTabs();
    if (selectedValue !== value) {
        return null;
    }
    return (_jsx("div", { ref: ref, className: cn("mt-2 ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2", className), ...props }));
});
TabsContent.displayName = "TabsContent";
export { Tabs, TabsList, TabsTrigger, TabsContent };
