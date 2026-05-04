import request from './request'
import type { Account } from '../types'

export function registerAccount(data: Partial<Account>) {
  return request({
    url: '/accounts/register',
    method: 'post',
    data
  })
}

export function getAccountList() {
  return request({
    url: '/accounts',
    method: 'get'
  })
}
