import { useEffect, useMemo, useState } from 'react'
import { t, useLanguage } from './i18n'
import type { DirectorController } from './controller'
import type { DirectorJob, DirectorSnapshot, TaskProject, VdRun } from './types'
import { CloseIcon } from './icons'
import { ArtifactPreviewDialog, ArtifactThumbnail, previewArtifactsFromResult, type PreviewArtifact } from './ArtifactPreview'

const swallow = (): void => {}

interface JobGroup {
  id: string
  project: TaskProject
  workflowRun?: VdRun
  jobs: DirectorJob[]
  startedAt: string
}

function jobGroupStatus(group: JobGroup): DirectorJob['status'] | VdRun['status'] {
  if (group.workflowRun !== undefined) return group.workflowRun.status
  if (group.jobs.some(job => job.status === 'running')) return 'running'
  if (group.jobs.some(job => job.status === 'queued')) return 'queued'
  if (group.jobs.some(job => job.status === 'failed')) return 'failed'
  if (group.jobs.some(job => job.status === 'orphaned')) return 'orphaned'
  if (group.jobs.every(job => job.status === 'cancelled')) return 'cancelled'
  return 'completed'
}

export function JobDrawer({
  snapshot,
  director,
  onClose,
}: {
  snapshot: DirectorSnapshot
  director: DirectorController
  onClose(): void
}) {
  useLanguage()
  const [workflowId, setWorkflowId] = useState('')
  const [refreshError, setRefreshError] = useState<string | null>(null)
  const [openArtifact, setOpenArtifact] = useState<PreviewArtifact | null>(null)
  useEffect(() => {
    const abort = new AbortController()
    let pending = false
    const refresh = async (): Promise<void> => {
      if (pending) return
      pending = true
      try {
        await director.refreshTasks(abort.signal)
        if (!abort.signal.aborted) setRefreshError(null)
      } catch (error) {
        if (!abort.signal.aborted) setRefreshError(error instanceof Error ? error.message : String(error))
      } finally { pending = false }
    }
    void refresh()
    const timer = setInterval(() => { void refresh() }, 2_000)
    return () => { abort.abort(); clearInterval(timer) }
  }, [director])
  useEffect(() => {
    if (workflowId !== '' && !snapshot.taskProjects.some(project => project.id === workflowId)) setWorkflowId('')
  }, [snapshot.taskProjects, workflowId])
  const exportWorkflow = async (runId: string, projectId: string): Promise<void> => {
    const exported = await director.exportVdWorkflow(runId, projectId)
    const url = URL.createObjectURL(new Blob([exported.text], { type: 'application/json' }))
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = exported.filename
    anchor.click()
    setTimeout(() => URL.revokeObjectURL(url), 1_000)
  }
  const groups = useMemo<JobGroup[]>(() => {
    const groups: JobGroup[] = []
    for (const project of snapshot.taskProjects) {
      if (workflowId !== '' && project.id !== workflowId) continue
      const byId = new Map<string, JobGroup>()
      const runs = new Map(project.runs.map(run => [run.id, run]))
      for (const run of snapshot.workflowRuns) {
        if (run.projectId === project.id) runs.set(run.id, run)
      }
      for (const run of runs.values()) {
        byId.set(run.id, { id: run.id, project, workflowRun: run, jobs: [], startedAt: run.startedAt })
      }
      for (const job of [...project.jobs].reverse()) {
        const id = job.workflowRunId ?? `job:${job.id}`
        const existing = byId.get(id)
        if (existing !== undefined) existing.jobs.push(job)
        else byId.set(id, { id, project, jobs: [job], startedAt: job.createdAt })
      }
      groups.push(...byId.values())
    }
    return groups.sort((left, right) => right.startedAt.localeCompare(left.startedAt))
  }, [snapshot.taskProjects, snapshot.workflowRuns, workflowId])

  return (
    <aside className="vd-job-drawer" aria-label={t("任务列表")}>
      <header>
        <div>
          <strong>{t("任务")}</strong>
          <small>{t('Workflow runs and tasks across all workflows')}</small>
        </div>
        <button type="button" className="vd-close-icon-button" aria-label={t("关闭任务列表")} onClick={onClose}><CloseIcon /></button>
      </header>
      <div className="vd-job-filter">
        <label htmlFor="vd-task-workflow-filter">{t('Workflow')}</label>
        <select id="vd-task-workflow-filter" aria-label={t('Filter tasks by workflow')} value={workflowId}
          onChange={event => setWorkflowId(event.target.value)}>
          <option value="">{t('All workflows')}</option>
          {snapshot.taskProjects.map(project => <option key={project.id} value={project.id}>{project.name}</option>)}
        </select>
        {refreshError === null ? null : <p role="status">{t('Could not refresh tasks: {0}', refreshError)}</p>}
      </div>
      <div className="vd-job-list">
        {groups.length === 0 ? <p className="vd-job-empty">{t("尚无运行记录。")}</p> : groups.map(group => {
          const status = jobGroupStatus(group)
          const active = status === 'queued' || status === 'running'
          const groupedWorkflow = group.workflowRun !== undefined || group.jobs[0]?.workflowRunId !== undefined
          const completedJobs = group.workflowRun?.completedJobs
            ?? group.jobs.filter(job => !['queued', 'running'].includes(job.status)).length
          const totalJobs = group.workflowRun?.totalJobs ?? group.jobs.length
          return (
            <section key={`${group.project.id}:${group.id}`} className={`vd-job-group is-${status}`}>
              <header>
                <div>
                  <span className="vd-job-workflow-name" title={group.project.name}>{group.project.name}</span>
                  <strong>{groupedWorkflow ? t("工作流运行") : t("单节点运行")}</strong>
                  <small>{new Date(group.startedAt).toLocaleString()}</small>
                </div>
                <span className="vd-job-status">{t(status)}</span>
              </header>
              {groupedWorkflow ? (
                <div className="vd-job-summary">
                  <span>{group.workflowRun?.mode ?? group.jobs[0]?.workflowRunMode ?? 'workflow'}</span>
                  <span>{String(group.workflowRun?.batchSize ?? group.jobs[0]?.batchSize ?? 1)} {t("批")}</span>
                  <span>{String(completedJobs)} / {String(totalJobs)}</span>
                  {group.workflowRun !== undefined ? <>
                    <button type="button" onClick={() => { void director.openVdWorkflow(group.id, group.project.id).catch(swallow) }}>{t("打开工作流")}</button>
                    <button type="button" onClick={() => { void exportWorkflow(group.id, group.project.id).catch(swallow) }}>{t("导出工作流")}</button>
                  </> : null}
                  {active ? (
                    <button type="button" className="is-cancel" onClick={() => { void director.cancelVdRun(group.id, group.project.id).catch(swallow) }}>{t("取消运行")}</button>
                  ) : null}
                </div>
              ) : null}
              {group.workflowRun?.error !== undefined ? <p className="vd-job-error">{group.workflowRun.error}</p> : null}
              <div className="vd-job-rows">
                {group.jobs.map(job => {
                  const jobActive = job.status === 'queued' || job.status === 'running'
                  const retryable = job.status === 'failed' || job.status === 'cancelled' || job.status === 'orphaned'
                  const artifacts = previewArtifactsFromResult(job.result)
                  return (
                    <article key={job.id}>
                      <div className="vd-job-row-title">
                        <strong>{group.project.nodes.find(node => node.id === job.nodeId)?.title ?? job.nodeId}</strong>
                        <span>{job.providerId}</span>
                      </div>
                      <div className="vd-job-row-meta">
                        <span>{job.status} · {job.phase}</span>
                        {job.promptId === undefined ? null : <span title={job.promptId}>ComfyUI: {job.promptId}</span>}
                        {job.batchIndex === undefined ? null : <span>{t("批次")} {String(job.batchIndex + 1)}</span>}
                        <span>{String(Math.round(job.progress * 100))}%</span>
                      </div>
                      <div className="vd-job-progress"><i style={{ width: `${String(Math.round(job.progress * 100))}%` }} /></div>
                      {job.error !== undefined ? <p>{job.error}</p> : null}
                      {artifacts.length === 0 ? null : (
                        <div className="vd-job-artifacts" aria-label={t("任务产物")}>
                          {artifacts.map(artifact => (
                            <ArtifactThumbnail key={artifact.id} artifact={artifact} variant="job" onOpen={setOpenArtifact} />
                          ))}
                        </div>
                      )}
                      <div className="vd-job-row-actions">
                        {jobActive && !groupedWorkflow ? (
                          <button type="button" onClick={() => { void director.cancelJob(job.id, group.project.id).catch(swallow) }}>{t("取消")}</button>
                        ) : retryable && group.project.nodes.some(node => node.id === job.nodeId) ? (
                          <button type="button" onClick={() => { void director.runNode(job.nodeId, group.project.id).catch(swallow) }}>{t("重试节点")}</button>
                        ) : null}
                        {!jobActive ? (
                          <button
                            type="button"
                            className="is-delete"
                            onClick={() => {
                              if (!window.confirm(t('Delete this task record? Workflow assets will be kept.'))) return
                              void director.deleteJob(job.id, group.project.id).catch(swallow)
                            }}
                          >{t("删除")}</button>
                        ) : null}
                      </div>
                    </article>
                  )
                })}
              </div>
            </section>
          )
        })}
      </div>
      {openArtifact === null ? null : (
        <ArtifactPreviewDialog artifact={openArtifact} onClose={() => setOpenArtifact(null)} />
      )}
    </aside>
  )
}
