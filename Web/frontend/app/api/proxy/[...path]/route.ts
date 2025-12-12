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
    let apiPath = pathSegments.join('/');
    
    // 如果路径以 'api/' 开头，去掉它（因为前端代码中已经包含了 /api/ 前缀）
    // 例如：/api/proxy/api/auth/login -> pathSegments = ['api', 'auth', 'login']
    // 需要去掉开头的 'api'，变成 'auth/login'
    if (apiPath.startsWith('api/')) {
      apiPath = apiPath.substring(4);
    } else if (pathSegments[0] === 'api' && pathSegments.length > 1) {
      // 如果第一个段是 'api'，去掉它
      apiPath = pathSegments.slice(1).join('/');
    }
    
    const url = new URL(request.url);
    const queryString = url.search;
    const backendUrl = `${BACKEND_URL}/api/${apiPath}${queryString}`;
    
    // 调试日志（生产环境可以移除）
    if (process.env.NODE_ENV === 'development') {
      console.log(`[Proxy] ${method} ${request.url} -> ${backendUrl}`);
    }

    // 获取请求头（排除一些不需要的头部）
    const headers: HeadersInit = {};
    request.headers.forEach((value, key) => {
      // 排除 host, connection 等头部
      const lowerKey = key.toLowerCase();
      if (
        !['host', 'connection', 'content-length', 'referer'].includes(lowerKey)
      ) {
        headers[key] = value;
      }
    });
    
    // 确保 Content-Type 正确设置
    if (!headers['Content-Type'] && method !== 'GET' && method !== 'HEAD') {
      headers['Content-Type'] = 'application/json';
    }

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

