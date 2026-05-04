import { request } from '../utils/request'

export interface ComplianceCheckRequest {
  text: string
  platform: string
}

export interface ComplianceCheckResponse {
  passed: boolean
  has_violations?: boolean
  violations?: string[]
  cleaned_text?: string
  error?: string
}

export interface ContentComplianceRequest {
  title: string
  content: string
  platform: string
}

export interface ContentComplianceResponse {
  passed: boolean
  field?: 'title' | 'content'
  violations?: string[]
  error?: string
}

export function checkCompliance(data: ComplianceCheckRequest): Promise<ComplianceCheckResponse> {
  return request.post('/compliance/check', null, {
    params: {
      text: data.text,
      platform: data.platform
    }
  })
}

export function checkContentCompliance(data: ContentComplianceRequest): Promise<ContentComplianceResponse> {
  return new Promise((resolve, reject) => {
    checkCompliance({ text: data.title, platform: data.platform })
      .then(titleResult => {
        if (titleResult.has_violations) {
          resolve({
            passed: false,
            field: 'title',
            violations: titleResult.violations,
            error: `Title contains violations: ${titleResult.violations?.join(', ')}`
          })
          return
        }
        
        return checkCompliance({ text: data.content, platform: data.platform })
      })
      .then(contentResult => {
        if (!contentResult) return
        
        if (contentResult.has_violations) {
          resolve({
            passed: false,
            field: 'content',
            violations: contentResult.violations,
            error: `Content contains ${contentResult.violations?.length || 0} violation(s)`
          })
        } else {
          resolve({
            passed: true
          })
        }
      })
      .catch(reject)
  })
}
