import { NextRequest, NextResponse } from 'next/server';

/**
 * API 代理路由
 * 前端通过此代理访问后端 API，避免暴露后端地址和 CORS 问题
 * 服务端可以安全地访问 localhost:8000
 */
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  return handleRequest(request, path, 'GET');
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  return handleRequest(request, path, 'POST');
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  return handleRequest(request, path, 'PUT');
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  return handleRequest(request, path, 'DELETE');
}

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  return handleRequest(request, path, 'PATCH');
}

async function handleRequest(
  request: NextRequest,
  pathSegments: string[],
  method: string
) {
  try {
    // 构建后端 API 路径
    const apiPath = pathSegments.join('/');
    const url = new URL(request.url);
    const queryString = url.search;
    const backendUrl = `${BACKEND_URL}/api/${apiPath}${queryString}`;

    // 获取请求头（排除一些不需要的头部）
    const headers: HeadersInit = {};
    request.headers.forEach((value, key) => {
      // 排除 host, connection 等头部
      if (
        !['host', 'connection', 'content-length'].includes(key.toLowerCase())
      ) {
        headers[key] = value;
      }
    });

    // 获取请求体
    let body: BodyInit | undefined;
    if (method !== 'GET' && method !== 'HEAD') {
      try {
        body = await request.text();
      } catch (e) {
        // 如果没有请求体，忽略错误
      }
    }

    // 转发请求到后端
    const response = await fetch(backendUrl, {
      method,
      headers,
      body,
    });

    // 获取响应数据
    const data = await response.text();
    let jsonData;
    try {
      jsonData = JSON.parse(data);
    } catch {
      jsonData = data;
    }

    // 返回响应
    return NextResponse.json(jsonData, {
      status: response.status,
      statusText: response.statusText,
      headers: {
        'Content-Type': response.headers.get('Content-Type') || 'application/json',
      },
    });
  } catch (error: any) {
    console.error('Proxy error:', error);
    return NextResponse.json(
      { detail: error.message || 'Proxy request failed' },
      { status: 500 }
    );
  }
}

