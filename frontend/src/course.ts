import type { Course, CourseModule } from './types'

export function courseModules(course: Course): CourseModule[] {
  return course.outline.modules?.length ? course.outline.modules : [{ id: 'module-1', title: course.outline.module_title, objectives: course.outline.objectives, selected_passage_ids: course.outline.selected_passage_ids ?? [], assignments: course.options.assignments, quizzes: course.options.quizzes }]
}

export function moduleForSection(course: Course, moduleId?: string) {
  return moduleId ?? courseModules(course)[0]?.id
}
