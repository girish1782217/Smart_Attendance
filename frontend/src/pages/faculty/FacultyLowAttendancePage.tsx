import { LowAttendanceReport } from '../../components/reports/LowAttendanceReport'
import { PageHeader } from '../../components/PageHeader'

export function FacultyLowAttendancePage() {
  return (
    <div className="flex flex-col gap-5">
      <PageHeader title="Low Attendance" description="Students currently below the low-attendance threshold." />
      <LowAttendanceReport />
    </div>
  )
}
