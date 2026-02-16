'use client';

import { Search, PenTool, CheckCircle, Send } from 'lucide-react';

interface StepIndicatorProps {
  currentStep: number;
}

const steps = [
  { number: 1, label: 'Recherche', icon: Search, key: 'research' },
  { number: 2, label: 'Rédaction', icon: PenTool, key: 'writing' },
  { number: 3, label: 'Validation', icon: CheckCircle, key: 'validation' },
  { number: 4, label: 'Publication', icon: Send, key: 'publication' },
];

export default function StepIndicator({ currentStep }: StepIndicatorProps) {
  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg border border-gray-200 dark:border-slate-700 p-8">
      <div className="flex items-center justify-between">
        {steps.map((step, index) => {
          const Icon = step.icon;
          const isActive = currentStep === step.number;
          const isCompleted = currentStep > step.number;
          const isPending = currentStep < step.number;

          return (
            <div key={step.key} className="flex items-center flex-1">
              {/* Step Circle */}
              <div className="flex flex-col items-center flex-1">
                <div
                  className={`
                    flex items-center justify-center w-12 h-12 rounded-full border-2 transition-all
                    ${
                      isActive
                        ? 'bg-blue-500 border-blue-500 text-white'
                        : isCompleted
                          ? 'bg-green-500 border-green-500 text-white'
                          : 'bg-gray-100 dark:bg-slate-700 border-gray-300 dark:border-slate-600 text-gray-400 dark:text-slate-500'
                    }
                  `}
                >
                  {isCompleted ? (
                    <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                  ) : (
                    <Icon className="w-6 h-6" />
                  )}
                </div>
                <p
                  className={`mt-3 text-sm font-medium text-center transition-colors ${
                    isActive
                      ? 'text-blue-600 dark:text-blue-400'
                      : isCompleted
                        ? 'text-green-600 dark:text-green-400'
                        : 'text-gray-500 dark:text-slate-400'
                  }`}
                >
                  {step.label}
                </p>
              </div>

              {/* Connecting Line */}
              {index < steps.length - 1 && (
                <div
                  className={`flex-1 h-1 mx-4 transition-all rounded-full ${
                    isCompleted
                      ? 'bg-green-500'
                      : isActive
                        ? 'bg-blue-500'
                        : 'bg-gray-200 dark:bg-slate-600'
                  }`}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
