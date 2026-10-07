import { PageHeader } from '@/components/PageHeader'

export default function ComingSoonPage({ title }: { title: string }) {
  return (
    <>
      <PageHeader title={title} />
      <div className="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center text-sm text-slate-500">
        This page will be built in an upcoming step.
      </div>
    </>
  )
}