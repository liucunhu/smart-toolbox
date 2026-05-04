import request from './request'
import type { ContentTask } from '../types'

export function generateContent(data: { topic: string; platform: string }) {
  return request({
    url: '/content/generate',
    method: 'post',
    params: data
  })
}

export function checkCompliance(data: { text: string; platform: string }) {
  return request({
    url: '/compliance/check',
    method: 'post',
    params: data
  })
}
