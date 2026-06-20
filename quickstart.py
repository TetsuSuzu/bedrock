"""Boto3 クイックスタートのサンプル（ガイド準拠）。

実行前に仮想環境を有効化してください:
    # Windows (PowerShell)
    .\.venv\Scripts\Activate.ps1
    # macOS / Linux
    source .venv/bin/activate
"""

import boto3

# Amazon S3 を使用する
s3 = boto3.resource("s3")


def list_buckets():
    """すべてのバケット名を出力する。"""
    for bucket in s3.buckets.all():
        print(bucket.name)


def upload_example():
    """新しいファイルをアップロードする（バケットが存在する前提）。"""
    with open("test.jpg", "rb") as data:
        s3.Bucket("amzn-s3-demo-bucket").put_object(Key="test.jpg", Body=data)


if __name__ == "__main__":
    print("Buckets:")
    list_buckets()
