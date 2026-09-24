export function ErrorState({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  // Covers ApiError (a subclass) too -- previously only ApiError.message was
  // trusted, so a plain `new Error('...')` (e.g. "no profile linked") fell
  // through to the generic fallback and hid the real, actionable message.
  const message = error instanceof Error ? error.message : 'Something went wrong. Please try again.'
  return (
    <div
      role="alert"
      className="flex flex-col items-center gap-3 rounded-lg border border-red-200 bg-red-50 px-6 py-8 text-center"
    >
      <p className="text-sm font-medium text-red-800">{message}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="rounded-md border border-red-300 bg-white px-3 py-1.5 text-sm font-medium text-red-700 hover:bg-red-100"
        >
          Try again
        </button>
      )}
    </div>
  )
}
