<?xml version="1.0" encoding="UTF-8"?>
<!-- 选课导入格式转换: 统一集成选课格式 → 各学院可导入的格式 -->
<!-- 参数: target_college = A|B|C -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="xml" encoding="UTF-8" indent="yes"/>
  <xsl:param name="target_college">A</xsl:param>

  <xsl:template match="/">
    <xsl:choose>
      <!-- 学院A 导入格式 -->
      <xsl:when test="$target_college='A'">
        <Enrollments>
          <xsl:for-each select="Choices/choice">
            <Enrollment>
              <sno><xsl:value-of select="sid"/></sno>
              <cno><xsl:value-of select="cid"/></cno>
              <grd><xsl:value-of select="score"/></grd>
            </Enrollment>
          </xsl:for-each>
        </Enrollments>
      </xsl:when>

      <!-- 学院B 导入格式 -->
      <xsl:when test="$target_college='B'">
        <enrollments>
          <xsl:for-each select="Choices/choice">
            <enrollment>
              <sid><xsl:value-of select="sid"/></sid>
              <cid><xsl:value-of select="cid"/></cid>
            </enrollment>
          </xsl:for-each>
        </enrollments>
      </xsl:when>

      <!-- 学院C 导入格式 -->
      <xsl:when test="$target_college='C'">
        <Choices>
          <xsl:for-each select="Choices/choice">
            <choice>
              <Sno><xsl:value-of select="sid"/></Sno>
              <Cno><xsl:value-of select="cid"/></Cno>
              <Grd><xsl:value-of select="score"/></Grd>
            </choice>
          </xsl:for-each>
        </Choices>
      </xsl:when>

      <!-- 默认: 保持统一格式 -->
      <xsl:otherwise>
        <xsl:copy-of select="."/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

</xsl:stylesheet>
